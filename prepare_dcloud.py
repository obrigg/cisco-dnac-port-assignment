# If using dCloud's "Cisco Enterprise Networks Hardware Sandbox v1"
# lab - this script will prepare the switches for discovery
# and discover them

import os, time
from netmiko import ConnectHandler
from dnacentersdk import api
import requests
requests.packages.urllib3.disable_warnings()

def ConfigureDevice(switches):
    for switch in switches:
        net_connect = ConnectHandler(**switch)
        net_connect.enable()
        net_connect.send_config_set([
            'snmp-server community ro ro',
            'snmp-server community rw rw'],
            cmd_verify=False)

def CreateDiscovery():
    taskId = dnac.discovery.start_discovery(name="dcloud", discoveryType="Range",
        ipAddressList="198.18.128.23-198.18.128.24", snmpROCommunity="ro",
        snmpRWCommunity="rw", protocolOrder="SSH", userNameList=[dcloud_user],
        passwordList=[dcloud_password], enablePasswordList=[dcloud_password],
        snmpVersion="2c")
    taskStatus = dnac.task.get_task_by_id(taskId['response']['taskId'])
    if taskStatus['isError'] == True:
        raise Exception (" **** Discovery task Creation FAILED ****")

def AssignDevicesToSite(switches):
    sites = dnac.sites.get_site()
    for site in sites['response']:
        if site['name'] == "NTN01":
            siteId = site['id']
    for switch in switches:
        dnac.sites.assign_device_to_site(device=[{"ip":switch['host']}], site_id=siteId)

print("\n\n\n\n\tGetting the environment variables ready...")
dcloud_user = "admin"
dcloud_password = "C1sco12345"
os.environ["DNAC"] = "198.18.129.100"
os.environ["DNAC_USER"] = dcloud_user
os.environ["DNAC_PASSWORD"] = dcloud_password
from config import DNAC, DNAC_PORT, DNAC_USER, DNAC_PASSWORD, DNAC_VERSION, project_name, template_name, profile_name
dcloud_area =       {"type": "area",
                    "site": {
                        "area": {
                        "name": "Israel",
                        "parentName": "Global"},
                        "building": {
                        "name": "NTN01",
                        "address": "Netanya"}}}
dcloud_building =   {"type": "building",
                    "site": {
                        "area": {
                        "name": "Israel",
                        "parentName": "Global"},
                        "building": {
                        "name": "NTN01",
                        "address": "Netanya"}}}

print("\tConfiguring SNMP on the switches")
C9300 = {"device_type":"cisco_xe",
        "host":"198.18.128.23",
        "username": dcloud_user,
        "password": dcloud_password,
        "secret": dcloud_password,
        "port" : 22
        }
C3850 = {"device_type":"cisco_xe",
        "host":"198.18.128.24",
        "username": dcloud_user,
        "password": dcloud_password,
        "secret": dcloud_password,
        "port" : 22
        }
switches = [C9300, C3850]
ConfigureDevice(switches)

print("\tConnecting to Cisco DNA Center")
dnac = api.DNACenterAPI(username=DNAC_USER,
                            password=DNAC_PASSWORD,
                            base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                            version=DNAC_VERSION,
                            verify=False)
print("\tDiscovering the switches")
CreateDiscovery()
print("\tCreating area/site")
dnac.sites.create_site(payload=dcloud_area)
time.sleep(3)
dnac.sites.create_site(payload=dcloud_building)
print("\tWaiting 30 seconds to allow discovery to complete")
time.sleep(30)
print("\tAssociating the switches to the site")
AssignDevicesToSite(switches)
