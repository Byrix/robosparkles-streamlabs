#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
import codecs
import re
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
			self.HugCommand = "!hug"
			self.ComplimentCommand = "!compliment"
			self.Permission = "everyone"
			self.Users = ""
			self.Cooldown = 0

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
ScriptName = "WholesomeVibes"
Website = "twitch.tv/biosparkles"
Description = "Creates psuedo-random hug and compliment commands"
Creator = "Byrix"
Version = "1.0.1"

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = Settings()
global HugsFile
HugsFile = ""
global Hugs
Hugs = []

#---------------------------
#   Initialize Data (Only called on load)
#---------------------------
def Init():
    # Load settings
	global SettingsFile
	SettingsFile = os.path.join(os.path.dirname(__file__), "wholesome-settings.json")
	global ScriptSettings
	ScriptSettings = Settings(SettingsFile)

	global HugsFile
	HugsFile = os.path.join(os.path.dirname(__file__), "hugs.conf")

	LoadHugsFile()
	UpdatedUi()

	return

#---------------------------
#   Execute Data / Process messages
#---------------------------
def Execute(data):
	if data.IsChatMessage() and data.IsFromTwitch():
		# Check if message is a recognised command or a regular message

		comm = data.GetParam(0)
		isComm = False
		if comm == ScriptSettings.HugCommand:
			if not Parent.HasPermission(data.User, ScriptSettings.Permission, ScriptSettings.Users):
				# Parent.SendStreamMessage("PERMISSION MESSAGE")
				return
			elif Parent.IsOnCooldown(ScriptName, ScriptSettings.HugCommand):
				# Parent.SendStreamMessage("COOLDOWN MESSAGE")
				return

			target = GetTarget(data)
			if not target:
				Parent.SendStreamMessage("/me No target specified")
				return

			choice = Parent.GetRandom(0, len(Hugs))
			response = Parse(Hugs[choice], data.UserName, target)
			Parent.SendStreamMessage("/me {0}".format(response))
		elif comm==ScriptSettings.ComplimentCommand:
			if not Parent.HasPermission(data.User, ScriptSettings.Permission, ScriptSettings.Users) or Parent.IsOnCooldown(ScriptName, ScriptSettings.ComplimentCommand):
				return
			# Send a compliment
			apiResponse = Parent.GetRequest("https://complimentr.com/api", {})
			response = apiResponse.split("\"")[8]
			responseCorrect = ""
			for i in range(len(response)-1):
				if response[i]=='i' and response[i-1]==" " and (response[i+1]==" " or response[i+1]=="'"):
					responseCorrect += "I"
				elif i==0 and response[i]=="i" and (response[i+1]==" " or response[i+1]=="'"):
					responseCorrect += "I"
				else:
					responseCorrect += response[i]

			target = GetTarget(data)
			if not target:
				Parent.SendStreamMessage("/me No target specified")
				return

			response = "/me {0}, {1} <3 <3".format(target, responseCorrect)
			Parent.SendStreamMessage(response)
		else:
			return
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
	ui['HugCommand']['value'] = ScriptSettings.HugCommand
	ui['ComplimentCommand']['value'] = ScriptSettings.ComplimentCommand
	ui['Cooldown']['value'] = ScriptSettings.Cooldown
	ui['Permission']['value'] = ScriptSettings.Permission
	ui['Users']['value'] = ScriptSettings.Users

	try:
		with codecs.open(UiFilePath, encoding="utf-8-sig", mode="w+") as f:
			json.dump(ui, f, encoding="utf-8", indent=4, sort_keys=True)
	except Exception as err:
		sendError("{0}".format(err))
	return

def LoadHugsFile():
	try:
		with codecs.open(HugsFile, encoding="utf-8-sig", mode="r") as f:
			matches = []
			for line in f:
				line = line.strip()
				if len(line) > 0 and line[0] != "#":
					matches.append(line)
		global Hugs
		Hugs = matches
	except Exception as err:
		sendError("{0}".format(err))
	return

def GetTarget(data):
	if data.GetParam(1):
		target = data.GetParam(1).lower()
		if target[0] == "@":
			target = target[1:]
	return target
#---------------------------
#   Misc. Functions
#---------------------------
def sendError(msg):
	Parent.Log(ScriptName, msg)
	return

def EditHugFile():
    os.startfile(HugsFile)
    return
#---------------------------
#   Optional Functions
#---------------------------
def Parse(parseString, username, targetname):
	# Allows you to create your own customer $parameters
	parseString = parseString.replace("$username", username)
	parseString = parseString.replace("$targetname", targetname)
	return parseString

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
