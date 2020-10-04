import os
DNAC=os.environ.get('DNAC','sandboxdnac.cisco.com')
DNAC_USER=os.environ.get('DNAC_USER','devnetuser')
DNAC_PASSWORD=os.environ.get('DNAC_PASSWORD','Cisco123!')
DNAC_PORT=os.environ.get('DNAC_PORT',443)
DNAC_VERSION="1.3.3"
WEBEX_TEAMS_TOKEN=os.environ.get('WEBEX_TEAMS_TOKEN','Put your Spark Token here, without the Bearer!')
PROXY = {'https': 'http://proxy.if.relevant.com:80'}
AUTH_USERS = ['obrigg@cisco.com', 'rcsapo@cisco.com', 'eyelbaz@cisco.com']

project_name = "Vlan Assignment"
template_name = "Int_Vlan_template"
profile_name = "Int_Vlan_profile"
