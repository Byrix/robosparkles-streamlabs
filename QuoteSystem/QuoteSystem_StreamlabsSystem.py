#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
import codecs
import re
from datetime import date
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
			self.CallCommand = "!quote"
			self.EditCommand = "!editquote"
			self.RemoveCommand = "!removequote"
			self.AddCommand = "!addquote"
			self.CallPermission = "everyone"
			self.AddPermission = "subscriber"
			self.EditPermission = "moderator"
			self.CallCooldown = 0
			self.EditCooldown = 0
			self.AddCooldown = 0
			self.ShowDate = True
			self.ShowGame = True
		self.Info = ""

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
ScriptName = "QuoteSystem"
Website = "twitch.tv/biosparkles"
Description = "Add, call and manage quotes - allows quote searching when calling"
Creator = "Byrix"
Version = "2.0.0"

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = Settings()
global QuotesFile
QuotesFile = ""
global Quotes
Quotes = []
global Auth
Auth = []

global PermissionMessage
PermissionMessage = "You don't have permission to use that command"
global CooldownMessage
CooldownMessage = "Command is on cooldown"
global QuoteExist
QuoteExist = "Quote #$quoteID doesn't exist"
global QuoteMatch
QuoteMatch = "No matching quotes were found"
global QuoteEdit
QuoteEdit = "$username -> updated quote #$quoteID"
global QuoteDelete
QuoteDelete = "$username -> deleted quote #$quoteID"
global BlankQuoteMessage
BlankQuoteMessage = "$username -> no changes specified"
global AddQuoteMessage
AddQuoteMessage = "$username -> quote #$quoteID added"

#---------------------------
#   Initialize Data (Only called on load)
#---------------------------
def Init():
    # Load settings
	global SettingsFile
	SettingsFile = os.path.join(os.path.dirname(__file__), "quote-settings.json")
	global ScriptSettings
	ScriptSettings = Settings(SettingsFile)
	global QuotesFile
	QuotesFile = os.path.join(os.path.dirname(__file__), "quotes.json")

	LoadQuotes()
	UpdatedUi()
	LoadAuth()

	return

#---------------------------
#   Execute Data / Process messages
#---------------------------
def Execute(data):
	if data.IsChatMessage() and data.IsFromTwitch():
		givenCommand = data.GetParam(0)
		if givenCommand == ScriptSettings.CallCommand:
			# Check permissions and cooldown
			if not Parent.HasPermission(data.User, ScriptSettings.CallPermission, ScriptSettings.Info):
				# Parent.SendStreamMessage(PermissionMessage.format(data.UserName))
				# sendMessage(Permissionmessage, data.UserName)
				return
			elif Parent.IsOnCooldown(ScriptName, ScriptSettings.CallCommand):
				# Parent.SendStreamMessage(CooldownMessage.format(data.UserName))
				# sendMessage(CooldownMessage, data.UserName)
				return

			# Check if specific quote or search
			givenParam = data.GetParam(1)
			if not givenParam:
				# Get a random quote
				quoteRef = Parent.GetRandom(0, len(Quotes))
				quote = Quotes[quoteRef]
			elif re.match("[0-9]+", givenParam):
				# Get a specific quote by index
				quoteRef = int(givenParam)-1
				if quoteRef < 0 or quoteRef >= len(Quotes):
					# Parent.SendStreamMessage(QuoteExist.format(data.UserName))
					sendMessage(QuoteExist, data.UserName)
					return

				quote = Quotes[quoteRef]
			else:
				# Get a quote from searching
				searchTerm = ""
				for i in range(1, data.GetParamCount()):
					if i!=1:
						searchTerm += " "
					searchTerm += data.GetParam(i)
				searchTerm = searchTerm.lower()

				matchedQuotes = []
				for i in range(0, len(Quotes)):
					quote = Quotes[i]
					if re.search(searchTerm, quote["quote"].lower()):
						matchedQuotes.append(i)
				if len(matchedQuotes) == 0:
					# Parent.SendStreamMessage(QuoteMatch.format(data.UserName))
					sendMessage(QuoteMatch, data.UserName)
					return
				else:
					randNum = Parent.GetRandom(0, len(matchedQuotes))
					quoteRef = matchedQuotes[randNum]
					quote = Quotes[quoteRef]

			# Format the quote for printing
			response = "/me Quote #{0}: {1}".format(quoteRef+1, quote["quote"])
			if ScriptSettings.ShowGame:
				response += " [{0}]".format(quote["game"])
			if ScriptSettings.ShowDate:
				response += " [{0}]".format(quote["date"])

			# Return the quote
			Parent.SendStreamMessage(response)
			Parent.AddCooldown(ScriptName, ScriptSettings.CallCommand, ScriptSettings.CallCooldown)
			return
		elif givenCommand == ScriptSettings.EditCommand:
			# Check permissions and cooldown
			if not Parent.HasPermission(data.User, ScriptSettings.EditPermission, ScriptSettings.Info):
				# Parent.SendStreamMessage(PermissionMessage.format(data.UserName))
				# Parent.Log(ScriptName, "1.1")
				# sendMessage(PermissionMessage, data.UserName)
				return
			elif Parent.IsOnCooldown(ScriptName, ScriptSettings.EditCommand):
				# Parent.SendStreamMessage(CooldownMessage.format(data.UserName))
				# Parent.Log(ScriptName, "1.2")
				# sendMessage(CooldownMessage, data.UserName)
				return

			# Get specified quote
			quoteRef = data.GetParam(1)
			if not re.match("[0-9]+", quoteRef):
				# Parent.SendStreamMessage(QuoteExist.format(data.UserName))
				# Parent.Log(ScriptName, "2")
				sendMessage(QuoteExist, data.UserName)
				return
			quoteRef = int(quoteRef)-1
			if quoteRef < 0 or quoteRef > len(Quotes):
				# Parent.SendStreamMessage(QuoteExist.format(data.UserName))
				# Parent.Log(ScriptName, "3")
				sendMessage(QuoteExist, data.UserName)
				return
			quote = Quotes[quoteRef]

			# Make relevant changes
			newQuote = ""
			for i in range(2,data.GetParamCount()):
				if i!=1:
					newQuote += " "
				newQuote += data.GetParam(i)
			if newQuote == "":
				# Parent.SendStreamMessage(BlankQuoteMessage.format(data.UserName))
				sendMesssage(BlankQuoteMessage, data.UserName)
				return
			quote['quote'] = newQuote
			Quotes[quoteRef] = quote

			# Return success message
			# Parent.SendStreamMessage(QuoteEdit.format(data.UserName, quoteRef))
			sendMessage(QuoteEdit, data.UserName, quoteRef+1)
			Parent.AddCooldown(ScriptName, ScriptSettings.EditCommand, ScriptSettings.EditCooldown)
			return
		elif givenCommand == ScriptSettings.RemoveCommand:
			# Check permissions and cooldown
			if not Parent.HasPermission(data.User, ScriptSettings.EditPermission, ScriptSettings.Info):
				# Parent.SendStreamMessage(PermissionMessage.format(data.UserName))
				# sendMessage(PermissionMessage, data.UserName)
				return
			elif Parent.IsOnCooldown(ScriptName, ScriptSettings.EditCommand):
				# Parent.SendStreamMessage(CooldownMessage.format(data.UserName))
				# sendMessage(CooldownMessage, data.UserName)
				return
			#
			# Get specified quote
			quoteRef = data.GetParam(1)
			if not re.match("[0-9]+", quoteRef):
				# Parent.SendStreamMessage(QuoteExist.format(data.UserName))
				# Parent.Log(ScriptName, "2")
				sendMessage(QuoteExist, data.UserName)
				return
			quoteRef = int(quoteRef)-1
			if quoteRef < 0 or quoteRef > len(Quotes):
				# Parent.SendStreamMessage(QuoteExist.format(data.UserName))
				# Parent.Log(ScriptName, "3")
				sendMessage(QuoteExist, data.UserName)
				return

			# Delete specified quote
			global Quotes
			Quotes.pop(quoteRef)
			# Parent.SendStreamMessage(QuoteDelete.format(data.UserName, quoteRef))
			sendMessage(QuoteDelete, data.UserName, quoteRef+1)
			Parent.AddCooldown(ScriptName, ScriptSettings.RemoveCommand, ScriptSettings.EditCooldown)

			for quoteInd in Quotes:
				if int(quoteInd) > int(quoteRef):
					Parent.Log(ScriptName, quoteInd)
					newInd = str(int(quoteInd)-1)
					newIndData = Quotes[quoteInd]
					del Quotes[quoteInd]
					Quotes[newInd] = newIndData
		elif givenCommand == ScriptSettings.AddCommand:
			# Check permissions and cooldown
			if not Parent.HasPermission(data.User, ScriptSettings.AddPermission, ScriptSettings.Info):
				# Parent.SendStreamMessage(PermissionMessage.format(data.UserName))
				# sendMessage(PermissionMessage, data.UserName)
				return
			elif Parent.IsOnCooldown(ScriptName, ScriptSettings.AddCommand):
				# Parent.SendStreamMessage(CooldownMessage.format(data.UserName))
				# sendMessage(CooldownMessage, data.UserName)
				return

			# Create quote
			newQuote = ""
			for i in range(1,data.GetParamCount()):
				if i!=1:
					newQuote += " "
				newQuote += data.GetParam(i)
			if newQuote == "":
				# Parent.SendStreamMessage(BlankQuoteMessage.format(data.UserName))
				sendMessage(BlankQuoteMessage, data.UserName)
				return

			actDate = date.today().strftime("%d/%m/%Y")

			# Parent.Log(ScriptName, str(len(Auth)))
			headers = {"client-id": Auth[0], 'Authorization': 'Bearer {0}'.format(Auth[1])}

			streamerInfo = Parent.GetRequest("https://api.twitch.tv/helix/users?login={0}".format(Parent.GetChannelName()), headers)
			broadcasterID = streamerInfo.split("\"")[10].strip("\\")

			channelInfo = Parent.GetRequest("https://api.twitch.tv/helix/channels?broadcaster_id={0}".format(broadcasterID), headers)
			currGame = channelInfo.split("\"")[26].strip("\\")

			# Add quote
			# quote = Quote(newQuote, actDate, currGame)
			quote = {"quote": newQuote, "date": actDate, "game": currGame, "addedBy": data.UserName}
			global Quotes
			Quotes.append(quote)
			# Parent.SendStreamMessage(AddQuoteMessage.format(data.UserName, quoteRef))
			sendMessage(AddQuoteMessage, data.UserName, len(Quotes))
			Parent.AddCooldown(ScriptName, ScriptSettings.AddCommand, ScriptSettings.AddCooldown)
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
	ui["CallCommand"]["value"] = ScriptSettings.CallCommand
	ui["CallPermission"]["value"] = ScriptSettings.CallPermission
	ui["CallCooldown"]["value"] = ScriptSettings.CallCooldown
	ui["ShowDate"]["value"] = ScriptSettings.ShowDate
	ui["AddCommand"]["value"] = ScriptSettings.AddCommand
	ui["AddPermission"]["value"] = ScriptSettings.AddPermission
	ui["AddCooldown"]["value"] = ScriptSettings.AddCooldown
	ui["EditCommand"]["value"] = ScriptSettings.EditCommand
	ui["RemoveCommand"]["value"] = ScriptSettings.RemoveCommand
	ui["EditPermission"]["value"] = ScriptSettings.EditPermission
	ui["EditCooldown"]["value"] = ScriptSettings.EditCooldown

	try:
		with codecs.open(UiFilePath, encoding="utf-8-sig", mode="w+") as f:
			json.dump(ui, f, encoding="utf-8", indent=4, sort_keys=True)
	except Exception as err:
		sendError("{0}".format(err))

def LoadQuotes():
	try:
		with codecs.open(QuotesFile, encoding="utf-8-sig", mode="r") as f:
			quotesJSON = json.load(f, encoding="utf-8")
			# Parent.Log(ScriptName, "Loading quotes: quotes loaded {0}".format(len(quotesJSON)))
	except Exception as err:
		sendError("LoadQuotes: Failed to load quotes: {0}".format(err))
		return

	global Quotes
	Quotes = quotesJSON
	return

def LoadAuth():
	try:
		with codecs.open(os.path.join(os.path.dirname(__file__), "apiAccess.conf")) as f:
			authData = []
			for line in f:
				line = line.strip()
				if len(line)>0 and line[0]!="#":
					# Parent.Log(ScriptName, line)
					authData.append(line.split(":")[1].strip(" "))
		global Auth
		Auth = authData
	except Exception as err:
		Parent.Log(ScriptName, "LoadAuth: {0}".format(err))
	# Parent.Log(ScriptName, str(len(Auth)))
	return

#---------------------------
#   Misc. Functions
#---------------------------
def sendError(msg):
	Parent.Log(ScriptName, msg)
	#Parent.SendStreamWhisper("byrix__", "{0}: {1}".format(ScriptName, msg))
	return

def sendMessage(msg, username, quoteID="-1"):
	response = Parse(msg, username, quoteID)
	Parent.SendStreamMessage("/me {0}".format(response))
	return

#---------------------------
#   Optional Functions
#---------------------------
def Parse(parseString, username, quoteID):
	# Allows you to create your own customer $parameters
	parseString = parseString.replace("$username", username)
	parseString = parseString.replace("$quoteID", str(quoteID))
	return parseString

def ReloadSettings(jsonData):
	# Called when a user clicks the Save Settings button
	ScriptSettings.Reload(jsonData)
	ScriptSettings.Save(SettingsFile)
	return

def Unload():
	try:
		with codecs.open(QuotesFile, encoding="utf-8-sig", mode="w+") as f:
			json.dump(Quotes, f, encoding="utf-8", indent=4, sort_keys=True)
	except Exception as err:
		sendError("{0}".format(err))
	return

def ScriptToggled(state):
	return
