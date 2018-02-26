#!/usr/bin/python
__author__ = "Fabian van der Hoeven"
__version__ = '0.1'
import os, sys
import argparse
import zabbix_api

discovery_checks_types = {
    'ssh': 0,
    'ldap': 1,
    'smtp': 2,
    'ftp': 3,
    'http': 4,
    'pop': 5,
    'nntp': 6,
    'imap': 7,
    'tcp': 8,
    'zabbix agent': 9,
    'snmpv1 agent': 10,
    'snmpv2 agent': 11,
    'icmp ping': 12,
    'snmpv3 agent': 13,
    'https': 14,
    'telnet': 15
}

def connectZabbix(host, user, password):
    zapi = zabbix_api.ZabbixAPI(server=host)
    try:
        zapi.login(user, password)
    except zabbix_api.ZabbixAPIException as e:
        print "Something went wrong. Probably wrong credentials"
        sys.exit(e.args[1])
    return zapi

class Config:
    def __init__(self, conf_file):
        import ConfigParser
        self.zabbix_url = None
        self.zabbix_user = None
        self.zabbix_password = None
        self.zabbix_drules = {}
        self.conf_file = conf_file
        if not os.path.exists(self.conf_file):
            print("Can't open config file %s" % self.conf_file)
            sys.exit(1)
        # Read common config
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.conf_file)

    def parse(self):
        # Parse common config
        try:
            self.zabbix_url = self.config.get('common', 'zabbix_url')
        except:
            self.zabbix_url = 'http://localhost'
        try:
            self.zabbix_user = self.config.get('common', 'zabbix_user')
        except:
            self.zabbix_user = 'Admin'
        try:
            self.zabbix_password = self.config.get('common', 'zabbix_password')
        except:
            self.zabbix_password = 'zabbix'
        sections = self.config.sections()
        for section in sections:
            if section <> 'common':
                #get parameters
                try:
                    iprange = self.config.get(section, 'iprange')
                except:
                    print "Parameter iprange not found. Cannot continue"
                    sys.exit(1)
                try:
                    interval = self.config.get(section, 'interval')
                except:
                    interval = '1h'
                try:
                    check_type = self.config.get(section, 'check_type')
                except:
                    print "Parameter check_type not found. Cannot continue"
                    sys.exit(1)
                if check_type <> 'icmp ping':
                    try:
                        check_ports = self.config.get(section, 'check_ports')
                    except:
                        print "Parameter check_ports not found. Cannot continue"
                        sys.exit(1)
                    if check_type == 'zabbix agent':
                        try:
                            key = self.config.get(section, 'check_key')
                        except:
                            print "Parameter check_key not found even though check type zabbix agent is selected. Cannot continue"
                            sys.exit(1)
                    else:
                        key = ''

                self.zabbix_drules[section] = {}
                self.zabbix_drules[section]['name'] = section
                self.zabbix_drules[section]['iprange'] = iprange
                self.zabbix_drules[section]['delay'] = interval
                self.zabbix_drules[section]['dchecks'] = []
                checks = {}
                checks['type'] = str(discovery_checks_types[check_type])
                checks['ports'] = check_ports
                checks['key_'] = key
                self.zabbix_drules[section]['dchecks'].append(checks)

parser = argparse.ArgumentParser(description='Create Zabbix discovery rules')
parser.add_argument("--config", dest="conf_file", metavar="FILE", help="file which contains configuration items", required=True)
args = parser.parse_args()

config = Config(args.conf_file)
config.parse()

zapi = connectZabbix(config.zabbix_url, config.zabbix_user, config.zabbix_password)
for drule in config.zabbix_drules:
    try:
        zapi.drule.create(config.zabbix_drules[drule])
    except zabbix_api.Already_Exists as e:
        print "Discovery rule '%s' allready exists" % drule
