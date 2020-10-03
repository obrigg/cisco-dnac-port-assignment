__author__ = "Oren Brigg"
__author_email__ = "obrigg@cisco.com"
__copyright__ = "Copyright (c) 2020 Cisco Systems, Inc."

import time
from dnacentersdk import api
from pprint import pprint
from config import DNAC, DNAC_PORT, DNAC_USER, DNAC_PASSWORD, DNAC_VERSION, project_name, template_name
import requests
requests.packages.urllib3.disable_warnings()

def GetSwitchList():
    # Connecting to DNAC
    global dnac
    dnac = api.DNACenterAPI(username=DNAC_USER,
                            password=DNAC_PASSWORD,
                            base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                            version=DNAC_VERSION,
                            verify=False)
    switches = dnac.devices.get_device_list(family='Switches and Hubs')
    return(switches['response'])

def GetPortList(switchX):
    # Connecting to DNAC
    global dnac
    dnac = api.DNACenterAPI(username=DNAC_USER,
                            password=DNAC_PASSWORD,
                            base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                            version=DNAC_VERSION,
                            verify=False)
    switches = GetSwitchList()
    ports = ["{:<30}{:<15}{:<21}{:<15}".format("Interface Name", "Admin", "Operational", "Vlan ID")]
    for switch in switches:
        if (switch['hostname'].lower() == switchX.lower()) or (switch['managementIpAddress'] == switchX):
            interfaces = dnac.devices.get_device_interfaces_by_specified_range(device_id=switch['id'],
                records_to_return=500, start_index=1)['response']
            for interface in interfaces:
                if interface['portType'] == 'Ethernet Port':
                    if interface['vlanId'] == None:
                        interface['vlanId'] = ""
                    port = "{:<30}{:<15}{:^21}{:^15}".format(interface['portName'], interface['adminStatus'], interface['status'], interface['vlanId'])
                    ports.append(port)
    return(ports)

def PortAssignment(deviceIp, interface, vlan):
    # Connecting to DNAC
    global dnac
    dnac = api.DNACenterAPI(username=DNAC_USER,
                            password=DNAC_PASSWORD,
                            base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                            version=DNAC_VERSION,
                            verify=False)
    projectId = CheckProject(project_name)
    print(f"\t\033[1;37;40mProject Id: {projectId}\033[0m")
    templateId = CheckTemplate(projectId, template_name)
    print(f"\t\033[1;37;40mTemplate Id: {templateId}\033[0m")
    params = {'vlan': vlan, 'int': interface}
    print(f"\t\033[1;37;40mParameters: {params}\033[0m")
    deploymentId = DeployTemplate(templateId, deviceIp, params)
    print(f"\t\033[1;37;40mDeployment Id: {deploymentId}\033[0m")
    return(IsDeploymentSuccessful)

def CheckProject(projectX):
    # Connecting to DNAC
    global dnac
    dnac = api.DNACenterAPI(username=DNAC_USER,
                            password=DNAC_PASSWORD,
                            base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                            version=DNAC_VERSION,
                            verify=False)
    projects = dnac.configuration_templates.get_projects()
    for project in projects:
        if project['name'] == projectX:
            return (project['id'])
    # If project does not exist:
    return(CreateProject(projectX))

def CreateProject(projectX):
    taskId = dnac.configuration_templates.create_project(name=projectX)
    time.sleep(2)
    taskStatus = dnac.task.get_task_by_id(taskId['response']['taskId'])
    if taskStatus['isError'] == True:
        raise Exception (" **** Project Creation FAILED ****")
    return(taskStatus['response']['data'])

def CheckTemplate(projectId, templateX):
    # Connecting to DNAC
    global dnac
    dnac = api.DNACenterAPI(username=DNAC_USER,
                            password=DNAC_PASSWORD,
                            base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                            version=DNAC_VERSION,
                            verify=False)
    templates = dnac.configuration_templates.gets_the_templates_available()
    for template in templates:
        if template['name'] == templateX:
            return (template['templateId'])
    return(CreateTemplate(projectId, templateX))

def CreateTemplate(projectId, templateX):
    content = """!
        interface $int
        switchport access vlan $vlan
        """
    templateParams = [{'parameterName': 'vlan', 'dataType': 'STRING', 'defaultValue': None,
        'description': None, 'required': True, 'notParam': False, 'paramArray': False,
        'displayName': None, 'instructionText': None, 'group': None, 'order': 2,
        'selection': None, 'range': [], 'key': None, 'provider': None, 'binding': ''},
        {'parameterName': 'int', 'dataType': 'STRING', 'defaultValue': None,
        'description': None, 'required': True, 'notParam': False, 'paramArray': False,
        'displayName': None, 'instructionText': None, 'group': None, 'order': 1,
        'range': [], 'key': None, 'provider': None, 'binding': ''}]
    taskId = dnac.configuration_templates.create_template(project_id=projectId, name=templateX,
        composite=False, deviceTypes=[{'productFamily': 'Switches and Hubs'}],
        templateParams=templateParams, softwareType="IOS-XE", templateContent=content)
    time.sleep(2)
    taskStatus = dnac.task.get_task_by_id(taskId['response']['taskId'])
    if taskStatus['isError'] == True:
        raise Exception (" **** Template Creation FAILED ****")
    templateId = taskStatus['response']['data']
    # Commit the template
    taskId = dnac.configuration_templates.version_template(templateId=templateId, comments="Initial commit")
    time.sleep(2)
    taskStatus = dnac.task.get_task_by_id(taskId['response']['taskId'])
    if taskStatus['isError'] == True:
        raise Exception (" **** Template Creation FAILED ****")
    return(templateId)

def DeployTemplate(templateId, deviceIp, params):
    targetInfo = [{'id': deviceIp, 'type': "MANAGED_DEVICE_IP", "params": params}]
    deploymentId = dnac.configuration_templates.deploy_template(forcePushTemplate=True,
        isComposite=False, templateId=templateId, targetInfo=targetInfo)
    time.sleep(2)
    id = deploymentId["deploymentId"].split()
    return (id[7])

def IsDeploymentSuccessful(deploymentId):
    time.sleep(5)
    results = dnac.configuration_templates.get_template_deployment_status(deployment_id=deploymentId)
    if results['status'] == "SUCCESS":
        return(True)
    else:
        return(False)
