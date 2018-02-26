#!/usr/bin/python
__author__ = "Fabian van der Hoeven"
__version__ = '0.1'
import os, sys
import argparse
import zabbix_api

host_interface_types = {
    'agent': 1,
    'snmp': 2,
    'ipmi': 3,
    'jmx': 4
}

def connectZabbix(host, user, password):
    zapi = zabbix_api.ZabbixAPI(server=host)
    try:
        zapi.login(user, password)
    except zabbix_api.ZabbixAPIException as e:
        print "Something went wrong. Probably wrong credentials"
        sys.exit(e.args[1])
    return zapi

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

class Config:
    def __init__(self, conf_file):
        import ConfigParser
        self.zabbix_url = None
        self.zabbix_user = None
        self.zabbix_password = None
        self.zabbix_jmxhosts = {}
        self.zapi = None
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
        self.zapi = connectZabbix(self.zabbix_url, self.zabbix_user, self.zabbix_password)
        sections = self.config.sections()
        for section in sections:
            if section <> 'common':
                #get parameters
                try:
                    port = self.config.get(section, 'port')
                except:
                    print "Parameter port not found. Cannot continue"
                    sys.exit(1)
                try:
                    templatename = self.config.get(section, 'template')
                except:
                    print "Parameter template not found. Cannot continue"
                    sys.exit(1)
                try:
                    hostgroup = self.config.get(section, 'hostgroup')
                except:
                    print "Parameter group not found. Cannot continue"
                    sys.exit(1)

                #configure host parameters + init interfaces, groups and templates
                self.zabbix_jmxhosts[section] = {}
                self.zabbix_jmxhosts[section]['host'] = args.host + ' - JMX - ' + section
                self.zabbix_jmxhosts[section]['interfaces'] = []
                self.zabbix_jmxhosts[section]['groups'] = []
                self.zabbix_jmxhosts[section]['templates'] = []
                #configure interface
                interface = {}
                interface['type'] = str(host_interface_types['jmx'])
                interface['port'] = port
                interface['main'] = '1'
                interface['useip'] = '0'
                interface['dns'] = args.host
                interface['ip'] = ''
                #configure group membership
                group = {}
                zhostgroup = self.zapi.hostgroup.get({'search':{'name':hostgroup}})
                if zhostgroup == []:
                    zhostgroup = self.zapi.hostgroup.create({'name':hostgroup})
                    hostgroupid = zhostgroup['groupids'][0]
                else:
                    hostgroupid = zhostgroup[0]['groupid']
                group['groupid'] = hostgroupid
                #configure template membership
                template = {}
                ztemplate = self.zapi.template.get({'search':{'name':templatename}})
                if ztemplate == []:
                    print "Template '%s' not found. Import it first in Zabbix. Cannot continue" % templatename
                    sys.exit(1)
                templateid = ztemplate[0]['templateid']
                template['templateid'] = templateid
                #append interface, group and template
                self.zabbix_jmxhosts[section]['interfaces'].append(interface)
                self.zabbix_jmxhosts[section]['groups'].append(group)
                self.zabbix_jmxhosts[section]['templates'].append(template)

parser = argparse.ArgumentParser(description='Create Zabbix JMX hosts')
parser.add_argument("--config", dest="conf_file", metavar="FILE", help="file which contains configuration items", required=True)
parser.add_argument("--host", dest="host", metavar="HOST", help="host to scan for available JMX applications", required=True)
args = parser.parse_args()

config = Config(args.conf_file)
config.parse()

#check if host is reachable
create_host = True
HOST_UP  = True if os.system("ping -c 1 -W 2 " + args.host + " > /dev/null 2>&1") is 0 else False
if not HOST_UP:
    create_host = query_yes_no("Host '%s' is not reachable. Are you sure you wish to create an entry with that host?" % args.host)
if not create_host:
    sys.exit(1)

for jmxhost in config.zabbix_jmxhosts:
    try:
        config.zapi.host.create(config.zabbix_jmxhosts[jmxhost])
    except zabbix_api.Already_Exists as e:
        print "JMX host '%s' allready exists" % config.zabbix_jmxhosts[jmxhost]['host']
