#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
import codecs
import re
import time as t
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

import clr
clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

# Construct a settings class
class Settings():
	def __init__(self, settingsfile=None):
		try:
			with codes.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
				self.__dict__ = json.load(f, encoding="utf-8")
		except:
			# Define default settings here
			self.Permission = "moderator"
			self.PermitCommand = "!permit"
			self.UnpermitCommand = "!unpermit"

	def Reload(self, jsondata):
		self.__dict__ = json.loads(jsondata, encoding="utf-8")

	def Save(self, settingsfile):
		try:
			with codecs.open(settingsfile, encoding="utf-8-sig", mode="w+") as f:
				json.dump(self.__dict__, f, encoding="utf-8")
			with codecs.open(settingsfile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
				f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding="utf-8")))
		except:
			sendError("Settings: Failed to save settings to file.")

#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "LinkProtection"
Website = "twitch.tv/biosparkles"
Description = "Stop links being posted in chat - permit users you trust"
Creator = "Byrix"
Version = "1.0.0"

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = Settings()

global TrustedUsers
TrustedUsers = []
global TempUsers
TempUsers = []

#---------------------------
#   Initialize Data (Only called on load)
#---------------------------
def Init():
    # Load settings
	global SettingsFile
	SettingsFile = os.path.join(os.path.dirname(__file__), "settings.json")
	global ScriptSettings
	ScriptSettings = Settings(SettingsFile)

	LoadTrusted()
	UpdatedUi()

	return

#---------------------------
#   Execute Data / Process messages
#---------------------------
def Execute(data):
	if data.IsChatMessage() and data.IsFromTwitch():
		# Check if command
		command = data.GetParam(0)
		if command == ScriptSettings.PermitCommand:
			if Parent.HasPermission(data.UserName, ScriptSettings.Permission, ""):
				target = data.GetParam(1).lower()
				if target == "":
					Parent.SendStreamMessage("/me No target specified")
				else:
					if target[0] == "@":
						target = target[1:]

					time = data.GetParam(2)
					if time:
						try:
							time = int(time)
						except Exception as err:
							# Parent.Log(ScriptName, "Excute: Invalid time")
							Parent.SendStreamMessage("/me Invalid time - defauling to 60s")
							time = 60
						if target in TrustedUsers:
							Parent.SendStreamMessage("/me {0} already has link permissions".format(target))
						else:
							global TempUsers
							TempUsers.append([target, time, t.time()])
							Parent.SendStreamMessage("/me @{0} has link permissions for {1} seconds".format(target, time))
					else:
						if target in TrustedUsers:
							Parent.SendStreamMessage("/me {0} already has link permissions".format(target))
						else:
							TrustedUsers.append(target)
							Parent.SendStreamMessage("/me @{0} now has link permissions.".format(target))
			else:
				return
		elif command == ScriptSettings.UnpermitCommand:
			target = data.GetParam(1).lower()
			if target == "":
				Parent.SendStreamMessage("/me No target specified")
			else:
				if target[0] == "@":
					target = target[1:]

				if target in TrustedUsers:
					TrustedUsers.remove(target)
					Parent.SendStreamMessage("/me {0} no longer has link permission".format(target))
				else:
					Parent.SendStreamMessage("/me {0} no longer has link permission".format(target))

		# Check if message contains a link
		message = ""
		for i in range(0, data.GetParamCount()):
			if i != 0:
				message += " "
			message += data.GetParam(i)
		user= data.UserName.lower()
		if re.search("(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}([-a-zA-Z0-9@:%_\+.~#?&//=]*)", message):
			if re.search("\.\.+", message):
				return

			# Is link, get bop hammer ready
			if Parent.HasPermission(user, ScriptSettings.Permission, "") or user in TrustedUsers:
				return
			for tUser in TempUsers:
				if user == tUser[0]:
					return

			msgID = re.search(";id=.*;", data.RawData).group(0).strip(";").split("=")[1].split(";")[0]
			Parent.SendStreamMessage("/delete {0}".format(msgID))
			Parent.SendStreamMessage("/me @{0}, no links in chat, please!".format(data.UserName))
	return

#---------------------------
#   Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
	if len(TempUsers) == 0:
		pass
	else:
		for i in range(len(TempUsers)):
			user = TempUsers[i]
			if t.time() - user[2] >= user[1]:
				TempUsers.pop(i)
			else:
				continue
	return

#---------------------------
#   Operating Functions
#---------------------------
def UpdatedUi():
	# Creates the UI
	ui = {}
	UiFilePath = os.path.join(os.path.dirname(__file__), "UI_Config.json")
	try:
		with codecs.open(UiFilePath, encoding="utf-8-sig", mode="r") as f:
			ui = json.load(f, encoding="utf-8")
	except Exception as err:
		sendError("{0}".format(err))

	# Update the UI with the loaded settings
	ui['Permission']['value'] = ScriptSettings.Permission
	ui['PermitCommand']['value'] = ScriptSettings.PermitCommand
	ui['UnpermitCommand']['value'] = ScriptSettings.UnpermitCommand

	try:
		with codecs.open(UiFilePath, encoding="utf-8-sig", mode="w+") as f:
			json.dump(ui, f, encoding="utf-8", indent=4, sort_keys=True)
	except Exception as err:
		sendError("{0}".format(err))

def LoadTrusted():
	UsersFile = os.path.join(os.path.dirname(__file__), "trustedUsers.txt")
	try:
		with open(UsersFile, 'r') as f:
			users = f.readline()
	except Exception as err:
		Parent.Log(ScriptName, "LoadTrusted: {0}".format(err))

	global TrustedUsers
	TrustedUsers = users.split(" ")
	return

#---------------------------
#   Misc. Functions
#---------------------------
def sendError(msg):
	Parent.Log(ScriptName, msg)
	# Parent.SendStreamWhisper("byrix__", "{0}: {1}".format(ScriptName, msg))
	return

def sendWhisper(user, msg):
	# Parent.SendStreamWhisper(user, msg)
	return

#---------------------------
#   Optional Functions
#---------------------------
def Parse(parseString, userid, username, targetid, targetname, message):
	# Allows you to create your own customer $parameters
    return parseString

def ReloadSettings(jsonData):
	# Called when a user clicks the Save Settings button
	ScriptSettings.Reload(jsonData)
	ScriptSettings.Save(SettingsFile)
	return

def Unload():
	# Called when a user reloads their scripts or closes the bot / cleanup stuff
	users = ""
	for user in TrustedUsers:
		users += "{0} ".format(user)

	UsersFile = os.path.join(os.path.dirname(__file__), "trustedUsers.txt")
	try:
		with open(UsersFile, 'w+') as f:
			f.write(users)
	except Exception as err:
		Parent.Log(ScriptName, "Unload: {0}".format(err))

	return

def ScriptToggled(state):
	return
