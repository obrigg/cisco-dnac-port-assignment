__author__ = "Oren Brigg"
__author_email__ = "obrigg@cisco.com"
__copyright__ = "Copyright (c) 2020 Cisco Systems, Inc."

import time
from pprint import pprint
from config import DNAC, DNAC_PORT, DNAC_USER, DNAC_PASSWORD, DNAC_VERSION, project_name, template_name, profile_name
import requests                                   # For RESTful calls
from requests.auth import HTTPBasicAuth           # For initial authentication w/ DNAC
requests.packages.urllib3.disable_warnings()      # Disable warnings. Living on the wild side..
from dnacentersdk import api

def getToken ():
    global token
    # Retrieves an authentication Token from Cisco DNA Center
    # Returns the Token
    url = f"https://{DNAC}:{DNAC_PORT}/api/system/v1/auth/token"
    res = requests.post(url=url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASSWORD), verify=False)
    token = res.json()['Token']
    return(res.json()['Token'])

def dnacGet (uri):
    # GET API call from Cisco DNA Center (to avoid repetition)
    url = f"https://{DNAC}:{DNAC_PORT}/{uri}"
    headers = {'Content-Type': "application/json", 'x-auth-token': token}
    body = ""
    res = requests.get(url=url, headers=headers, json=body, verify=False)
    return (res)

def dnacPost (uri, body):
    # POST API call from Cisco DNA Center (to avoid repetition)
    url = f"https://{DNAC}:{DNAC_PORT}/{uri}"
    headers = {'Content-Type': "application/json", 'x-auth-token': token}
    res = requests.post(url=url, headers=headers, json=body, verify=False)
    return (res)

###########################################################################

def CheckNetworkProfile(templateId):
    getToken()
    switchingProfiles = dnacGet("api/v1/siteprofile?namespace=switching").json()['response']
    for profile in switchingProfiles:
        if profile['name'] == profile_name:
            return(profile['siteProfileUuid'])
    CreateNetworkProfile(templateId)
    return(CheckNetworkProfile(templateId))

def CreateNetworkProfile(templateId):
    dnac = api.DNACenterAPI(username=DNAC_USER,
                            password=DNAC_PASSWORD,
                            base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                            version=DNAC_VERSION,
                            verify=False)
    body = {
    "siteProfileUuid": "",
    "version": 0,
    "name": profile_name,
    "namespace": "switching",
    "profileAttributes": [
        {
            "key": "cli.templates",
            "attribs": [
                {
                    "key": "device.family",
                    "value": "Switches and Hubs",
                    "attribs": [
                        {
                            "key": "device.series",
                            "value": "",
                            "attribs": [
                                {
                                    "key": "device.type",
                                    "value": "",
                                    "attribs": [
                                        {
                                            "key": "template.id",
                                            "value": templateId,
                                            "attribs": [
                                                {
                                                    "key": "template.version",
                                                    "value": "1"
                                                },
                                                {
                                                    "key": "template.name",
                                                    "value": template_name
                                                }
                                            ]
                                        },
                                        {
                                            "key": "device.tag",
                                            "value": "",
                                            "attribs": []
        }]}]}]}]}]}
    taskId = dnacPost("api/v1/siteprofile", body).json()
    taskStatus = dnac.task.get_task_by_id(taskId['response']['taskId'])
    if taskStatus['response']['isError'] == True:
        raise Exception (" **** Network Profile Creation FAILED ****")
    profileStart = taskStatus['response']['progress'].find("[")
    profileStop  = taskStatus['response']['progress'].find("]")
    profileId = taskStatus['response']['progress'][profileStart+1:profileStop]
    return(profileId)

def AssociateProfileToAllSites(profileId):
    dnac = api.DNACenterAPI(username=DNAC_USER,
                        password=DNAC_PASSWORD,
                        base_url="https://" + DNAC + ":" + str(DNAC_PORT),
                        version=DNAC_VERSION,
                        verify=False)
    sites = dnac.sites.get_site()['response']
    for site in sites:
        if site['name'] == "Global":
            break
    uri = f"api/v1/siteprofile/{profileId}/site/{site['id']}"
    taskId = dnacPost(uri, "").json()
    taskStatus = dnac.task.get_task_by_id(taskId['response']['taskId'])
    if taskStatus['response']['isError'] == True:
        raise Exception (" **** Network Profile Site Association FAILED ****")
    return(True)
