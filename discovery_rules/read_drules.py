#!/usr/bin/python
from zabbix_api import ZabbixAPI
import json
zapi = ZabbixAPI(server="http://zabbix.cmc-mgt.lan/")
zapi.login("fabian.vanderhoeven", "23091976")

print json.dumps(zapi.drule.get({"druleids": range(1,10)}), indent=2)

print json.dumps(zapi.dcheck.get({"druleids": range(1,10)}), indent=2)
#discovery check types
# 0 - (default) SSH;
# 1 - LDAP;
# 2 - SMTP;
# 3 - FTP;
# 4 - HTTP;
# 5 - POP;
# 6 - NNTP;
# 7 - IMAP;
# 8 - TCP;
# 9 - Zabbix agent;
# 10 - SNMPv1 agent;
# 11 - SNMPv2 agent;
# 12 - ICMP ping;
# 13 - SNMPv3 agent;
# 14 - HTTPS;
# 15 - Telnet.
