__author__ = "Oren Brigg"
__author_email__ = "obrigg@cisco.com"
__copyright__ = "Copyright (c) 2020 Cisco Systems, Inc."

from pprint import pprint
from dnac_functions import *
from dnac_private_functions import *
import json


def ProccessMessage(message):
    if "list switches" in message.text.lower():
        RequestSwitchList(message)
    elif "list ports" in message.text.lower():
        RequestPortList(message)
    elif "assign" in message.text.lower():
        RequestPortAssignment(message)
    else:
        InvalidInput(message)


def RequestSwitchList():
    print("Fetching the switch list...\n")
    try:
        switches = GetSwitchList()
        draft = "{:<30} {:<15}\n".format("Hostname", "IP Address")
        for switch in switches:
            draft += "{:<30} {:<15}\n".format(switch['hostname'], switch['managementIpAddress'])
    except:
            print(f"Oooops. Something went wrong trying to get the list of switches")
    print(draft)


def RequestPortList(message):
    print("Fetching the port list...")
    textSplit = message.text.split()
    i = 0
    isFound = False
    while i < len(textSplit):
        if textSplit[i].lower() == "ports" and (len(textSplit)-i == 2):
            isFound = True
            switch = textSplit[i+1]
            ports = GetPortList(switch)
            if len(ports) == 0:
                draft = f"The switch {switch} wasn't found.\n"
                print(draft)
            else:
                draft = f"Port list for switch: {switch}\n" + 60*"*" + "\n"
                for port in ports:
                    draft += f"{port}\n"
                print(draft)
        i += 1
    if not isFound:
        InvalidInput(message)


def RequestPortAssignment(sender, message):
    print("Working on the port assignment...")
    textSplit = message.text.split()
    i = 0
    isAssignmentOk = False
    while i < len(textSplit):
        if textSplit[i].lower() == "assign" and (len(textSplit)-i == 4):
            switchX = textSplit[i+1]
            interface = textSplit[i+2]
            vlan = textSplit[i+3]
            # TODO input validation
            switches = GetSwitchList()
            for switch in switches:
                if (switch['hostname'].lower() == switchX.lower()) or (switch['managementIpAddress'] == switchX):
                    try:
                        isAssignmentOk = PortAssignment(switch['managementIpAddress'], interface, vlan)
                    except:
                        pass
            if isAssignmentOk:
                draft = f"Success. Port {interface} on switch {switch['hostname']} is now assigned to vlan {vlan}"
                print(draft)
            else:
                draft = f"Oooops. Something went wrong trying to assign port {interface} on switch {switch['hostname']} to vlan {vlan}"
                print(draft)
        i += 1
    if not isAssignmentOk:
        draft = "Oooops. Something went wrong..."
        print(draft)


def InvalidInput(message):
    draft = "I didn't quite understand what you wrote.. I know that you're quite busy, so let's cut to the chase.\n"
    draft += f"I can help you assign switch ports to vlans. Use one of the following options:\n"
    draft += f"1. **List switches** - to get a list of available switches\n"
    draft += f"2. **List ports `switch hostname` (or `switch IP`)** - to get a list of ports on a given switch\n"
    draft += f"3. **Assign `switch IP` `interface` `vlan`** - to assign as interface to a vlan\n"
    print(draft)


if __name__ == '__main__':
    # Initialize Cisco DNA Center
    print(f"\nUsing Cisco DNAC Center: \033[1;32;40m {DNAC} \033[0m with user: \033[1;32;40m {DNAC_USER} \033[0m \n")
    try:
        dnac = api.DNACenterAPI(username=DNAC_USER,
                                password=DNAC_PASSWORD,
                                base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                                version=DNAC_VERSION,
                                verify=False)
    except:
        print("\t\033[1;31;40m ERROR: Failed to initialize Cisco DNA Center\033[0m")
    # Make sure Cisco DNA Center has a network profile/project/templates configured
    projectId = CheckProject(project_name)
    print(f"Project Name: {project_name} \t\t\tProject ID: {projectId}")
    templateId = CheckTemplate(projectId, template_name)
    print(f"Template Name: {template_name} \t\tTemplate ID: {templateId}")
    profileId = CheckNetworkProfile(templateId)
    print(f"Network Profile Name: {profile_name} \t\tNetwork Profile ID: {profileId}")
    AssociateProfileToAllSites(profileId)
    print("All sites are associated with the network profile")

    while True:
        draft  = f"Hello\n"
        draft += f"I can help you assign switch ports to vlans. Use one of the following options:\n"
        draft += f"1. **List switches** - to get a list of available switches\n"
        draft += f"2. **List ports `switch hostname` (or `switch IP`)** - to get a list of ports on a given switch\n"
        draft += f"3. **Assign `switch IP` `interface` `vlan`** - to assign as interface to a vlan\n"
        print(draft)

        user_input = input("So... What will it be? ")
        ProccessMessage(user_input)