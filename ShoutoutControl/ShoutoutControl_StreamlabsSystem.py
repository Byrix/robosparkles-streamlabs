#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
import codecs
import re
import time
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

import clr
clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

# Construct a settings class
class Settings():
	def __init__(self, settingsfile=None):
		try:
			with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
				self.__dict__ = json.load(f, encoding="utf-8")
		except:
			# Define default settings here
			self.Command = "!so"
			self.altCommands = ""
			self.Cooldown = 0
			self.Permission = "moderator"
			self.Users = ""
			self.Prefix = ""
			self.Suffix = "<3"
			self.RaidShoutout = False
			self.RaidWait = 30

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
ScriptName = "ShoutoutControl"
Website = "twitch.tv/biosparkles"
Description = "Shoutout command with personalised shoutouts depending on target"
Creator = "Byrix"
Version = "1.1.0"

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = Settings()
global ShoutoutsFile
ShoutoutsFile = ""
global PersonalShoutouts
PersonalShoutouts = {}

#---------------------------
#   Initialize Data (Only called on load)
#---------------------------
def Init():
    # Load settings
	global SettingsFile
	SettingsFile = os.path.join(os.path.dirname(__file__), "settings.json")
	global ScriptSettings
	ScriptSettings = Settings(SettingsFile)
	global ShoutoutsFile
	ShoutoutsFile = os.path.join(os.path.dirname(__file__), "shoutouts.conf")

	UpdatedUi()
	LoadShoutouts()

	return

#---------------------------
#   Execute Data / Process messages
#---------------------------
def Execute(data):
	if data.IsChatMessage() and data.IsFromTwitch():
		# Check if message is a !so or a regular message
		comm = data.GetParam(0)
		altCommands = ScriptSettings.altCommands.split(" ")
		isComm = False
		if comm==ScriptSettings.Command or comm in altCommands:
			isComm = True
		if not isComm:
			return

		# Check user had permission to make a shoutout and that command is not on cooldown
		if not Parent.HasPermission(data.User, ScriptSettings.Permission, ScriptSettings.Users):
			# Parent.SendStreamMessage("PERMISSION MESSAGE")
			return
		elif Parent.IsOnCooldown(ScriptName, ScriptSettings.Command):
			# Parent.SendStreamMessage("COOLDOWN MESSAGE")
			return

		# Check for target and personal shoutout message
		if data.GetParam(1):
			target = data.GetParam(1).lower()
			if target[0] == "@":
				target = target[1:]
		else:
			Parent.SendStreamMessage("/me No target specified")
			return

		createShoutout(data, target)
	elif data.IsRawData() and data.IsFromTwitch():
		if ScriptSettings.RaidShoutout and "USERNOTICE" in data.RawData and "msg-id=raid" in data.RawData:
			raidername = re.search("msg-param-login=.*;", data.RawData).group(0).strip(";").split("=")[1]

			time.sleep(ScriptSettings.RaidWait)
			createShoutout(data, raidername.lower())

	return

#---------------------------
#   Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
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
	ui['Command']['value'] = ScriptSettings.Command
	ui['altCommands']['value'] = ScriptSettings.altCommands
	ui['Cooldown']['value'] = ScriptSettings.Cooldown
	ui['Permission']['value'] = ScriptSettings.Permission
	ui['Users']['value'] = ScriptSettings.Users
	ui['Prefix']['value'] = ScriptSettings.Prefix
	ui['Suffix']['value'] = ScriptSettings.Suffix
	ui['RaidShoutout']['value'] = ScriptSettings.RaidShoutout
	ui['RaidWait']['value'] = ScriptSettings.RaidWait

	try:
		with codecs.open(UiFilePath, encoding="utf-8-sig", mode="w+") as f:
			json.dump(ui, f, encoding="utf-8", indent=4, sort_keys=True)
	except Exception as err:
		sendError("{0}".format(err))

def LoadShoutouts():
	try:
		with codecs.open(ShoutoutsFile, encoding="utf-8-sig", mode="r") as f:
			matches = {}
			for line in f:
				line = line.strip()
				if len(line) > 0 and line[0] != "#":
					user = line.split(" ")[0].lower()
					response = re.search("\".*\"", line).group(0).strip('"')
					matches[user] = response
		global PersonalShoutouts
		PersonalShoutouts = matches
	except Exception as err:
		sendError("{0}".format(err))
	return

def createShoutout(data, target):
	if target in PersonalShoutouts:
		response = PersonalShoutouts[target]
	else:
		response = PersonalShoutouts['default']

	# Send shoutout
	response = Parse(response, data.UserName, data.UserName, target, target, data.Message)
	prefix = Parse(ScriptSettings.Prefix, data.UserName, data.UserName, target, target, data.Message)
	suffix = Parse(ScriptSettings.Suffix, data.UserName, data.UserName, target, target, data.Message)

	response = "/me {0} {1} {2}".format(prefix.strip(), response.strip(), suffix.strip())

	Parent.SendStreamMessage(response)
	Parent.AddCooldown(ScriptName, ScriptSettings.Command, ScriptSettings.Cooldown)
	return

def Parse(parseString, userid, username, targetid, targetname, message):
	# Allows you to create your own customer $parameters
	parseString = parseString.replace("$userid", userid)
	parseString = parseString.replace("$username", username)
	parseString = parseString.replace("$targetname", targetname)
	parseString = parseString.replace("$url", "twitch.tv/{0}".format(targetname))
	return parseString

def EditConfigFile():
    os.startfile(ShoutoutsFile)
    return

#---------------------------
#   Misc. Functions
#---------------------------
def sendError(msg):
	Parent.Log(ScriptName, msg)
	return

#---------------------------
#   Optional Functions
#---------------------------
def ReloadSettings(jsonData):
	# Called when a user clicks the Save Settings button
	ScriptSettings.Reload(jsonData)
	ScriptSettings.Save(SettingsFile)
	return

def Unload():
	# Called when a user reloads their scripts or closes the bot / cleanup stuff
    return

def ScriptToggled(state):
	return
