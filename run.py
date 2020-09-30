__author__ = "Oren Brigg"
__author_email__ = "obrigg@cisco.com"
__copyright__ = "Copyright (c) 2020 Cisco Systems, Inc."

from webexteamssdk import WebexTeamsAPI
from pprint import pprint
from flask import Flask, request
from config import WEBEX_TEAMS_TOKEN, PROXY, AUTH_USERS
from dnac_functions import *
import json

def ProccessMessage(sender, message):
    if "list switches" in message.text.lower():
        RequestSwitchList(sender, message)
    elif "list ports" in message.text.lower():
        RequestPortList(sender, message)
    elif "assign" in message.text.lower():
        RequestPortAssignment(sender, message)
    else:
        InvalidInput(sender, message)
    return("Message received.")

def RequestSwitchList(sender, message):
    teams.messages.create(roomId=message.roomId, markdown="Fetching the switch list...")
    switches = GetSwitchList()
    draft = "{:<30} {:<15}\n".format("Hostname", "IP Address")
    for switch in switches:
        draft += "{:<30} {:<15}\n".format(switch['hostname'], switch['managementIpAddress'])
    teams.messages.create(roomId=message.roomId, text=draft)
    return("Message received.")

def RequestPortList(sender, message):
    teams.messages.create(roomId=message.roomId, markdown="Fetching the port list...")
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
                teams.messages.create(roomId=message.roomId, text=draft)
            else:
                draft = f"Port list for switch: {switch}\n" + 60*"*" + "\n"
                for port in ports:
                    draft += f"{port}\n"
                teams.messages.create(roomId=message.roomId, text=draft)
        i += 1
    if not isFound:
        InvalidInput(sender, message)
    return("Message received.")

def RequestPortAssignment(sender, message):
    teams.messages.create(roomId=message.roomId, markdown="Working on the port assignment...")
    textSplit = message.text.split()
    i = 0
    isAssignmentOk = False
    while i < len(textSplit):
        if textSplit[i].lower() == "assign" and (len(textSplit)-i == 4):
            switch = textSplit[i+1]
            interface = textSplit[i+2]
            vlan = textSplit[i+3]
            # TODO input validation
            try:
                isAssignmentOk = PortAssignment(switch, interface, vlan)
            except:
                pass
            if isAssignmentOk:
                draft = f"Success. Port {interface} on switch {switch} is now assigned to vlan {vlan}"
                teams.messages.create(roomId=message.roomId, markdown=draft)
            else:
                draft = f"Oooops. Something went wrong trying to assign port {interface} on switch {switch} to vlan {vlan}"
                teams.messages.create(roomId=message.roomId, markdown=draft)
        i += 1
    if not isAssignmentOk:
        draft = "Oooops. Something went wrong..."
        teams.messages.create(roomId=message.roomId, markdown=draft)
    return("Message received.")

def InvalidInput(sender, message):
    draft  = f"Hi {sender.nickName}\n"
    draft += "I didn't quite understand what you wrote.. I know that you're quite busy, so let's cut to the chase.\n"
    draft += f"I can help you assign switch ports to vlans. Use one of the following options:\n"
    draft += f"1. **List switches** - to get a list of available switches\n"
    draft += f"2. **List ports `switch hostname` (or `switch IP`)** - to get a list of ports on a given switch\n"
    draft += f"3. **Assign `switch IP` `interface` `vlan`** - to assign as interface to a vlan\n"
    teams.messages.create(roomId=message.roomId, markdown=draft)
    return("Message received.")

def InvalidUser(sender, message):
    draft  = f"Hi {sender.displayName},\n"
    draft += f"I'd call you {sender.nickName}, but we don't really know each other.\n"
    draft += f"This is quite awkward... but I'm not allowed to talk with strangers...\n"
    draft += f"I can't help you. But here's some kittens videos: https://www.youtube.com/results?search_query=kittens\n"
    teams.messages.create(roomId=message.roomId, markdown=draft)
    return("Message received.")

app = Flask(__name__)

@app.route('/', methods=['GET'])
def mainPage():
    return("cisco-dnac-port-association -> by Oren Brigg (obrigg@cisco.com)")

@app.route('/', methods=['POST'])
def index():
    """
    When messages come in from the webhook, they are processed here.
    The message text is parsed.  If an expected command is found in the message,
    further actions are taken.
    """
    webhook = json.loads(request.data.decode("utf-8"))
    message = teams.messages.get(webhook['data']['id'])
    sender = teams.people.get(personId=message.personId)
    isAuthUser = False
    for email in sender.emails:
        if email in AUTH_USERS:
            isAuthUser = True
            print(f"\n\tReceived the following message from \033[1;32;40m{sender.displayName}: '{message.text}'\n\033[0m 0;37;48m")
            return(ProccessMessage(sender, message))
        if email in bot.emails:
            isAuthUser = True
            return("BOT")
    if not isAuthUser:
        return(InvalidUser(sender, message))

if __name__ == '__main__':
    # Initialize Webex Teams API
    teams = WebexTeamsAPI(access_token=WEBEX_TEAMS_TOKEN) #, proxies=PROXY)
    bot = teams.people.me()
    # Clearing old webhooks and creating a new one
    webhooks = teams.webhooks.list()
    for webhook in webhooks:
        teams.webhooks.delete(webhook.id)
    webhook = input("Kindly enter the ngrok URL we'll be using (don't forget the 'https://' part): ")
    teams.webhooks.create(name="DNAC Bot", targetUrl=webhook, resource="messages", event="all")
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
