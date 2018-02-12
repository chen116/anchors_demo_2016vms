#!/usr/bin/env python

"""

"""

import sys
import os
import json
import signal
import copy
import logging

# From: http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
# Usage: print bcolors.WARNING + "Warning: No active frommets remain. Continue?" + bcolors.ENDC
# Alternatively use termcolor
class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

# This class just stores number of missed deadlines and allows for easy storage and access
class MissedDeadlines:
	def __init__(self):
		self.clear()
	def total(self):
		return sum(self.countPerTask.values())
	def update(self, pid, count):
		self.countPerTask[str(pid)] = count
	def clear(self):
		self.countPerTask = {}
	def __repr__(self):		# Used for interactive prompt
		return str(self.total())
	def __str__(self):		# Used for print
		return self.__repr__()	

# This class is for the local state of the application. It contains infomation on the 
# currently executing mode and parameters, in addition to the number of deadlines missed
class LocalState:
	KEY_MISSED_DEADLINES = "missedDeadlines"
	KEY_MODE = "modeName"
	KEY_PERIODS = "taskPeriods"
	KEY_EXEC_TIME = "taskExecTimes"
	KEY_APP_NAME = "appName"

	DEFAULT_APPNAME = "NoNameSet"
	DEFAULT_MODE = 0
	DEFAULT_EXECS = []
	DEFAULT_PERIODS = []

	def __init__(self, appName=None, modeName=None, execTimes=None, periods=None):
		logger = logging.getLogger(__name__)
	
		if appName == None:
			appName = LocalState.DEFAULT_APPNAME
		if modeName == None:
			modeName = LocalState.DEFAULT_MODE
		if execTimes == None:
			execTimes = LocalState.DEFAULT_EXECS
		if periods == None:
			periods = LocalState.DEFAULT_PERIODS

		self.state = {}
		self.state[LocalState.KEY_MISSED_DEADLINES] = MissedDeadlines()
		self.updateState(appName=appName, modeName=modeName, execTimes=execTimes, periods=periods)

		# Create aliases for simple access
		self.missedDeadlines = self.state[LocalState.KEY_MISSED_DEADLINES]

	def loadFromFile(self,fileHandle):
		logger = logging.getLogger(__name__)
		try:
			with open(fileHandle) as dataFile:
				tempJSON = json.load(dataFile)
			# Actually load the data into temp state
			state = {}
			state[LocalState.KEY_APP_NAME] = tempJSON[LocalState.KEY_APP_NAME]
			state[LocalState.KEY_MODE] =  tempJSON[LocalState.KEY_MODE]
			state[LocalState.KEY_EXEC_TIME] = tempJSON[LocalState.KEY_EXEC_TIME]
			state[LocalState.KEY_PERIODS] = tempJSON[LocalState.KEY_PERIODS]
			state[LocalState.KEY_MISSED_DEADLINES] = MissedDeadlines()

			# Assign to real local state
			self.state = state
			logger.info(bcolors.OKGREEN + "Successfully loaded from file" + bcolors.ENDC)
		except IOError as e:
			# No file exists
			logger.error( "IOError: " + str(e) )
			logger.error( bcolors.FAIL + "Failed to open %s, not loading"%(fileHandle) + bcolors.ENDC )
		except ValueError as e:
			# Error with formatting
			logger.error( "ValueError: " + str(e) )
			logger.error( bcolors.FAIL + "Failed to open %s, not loading"%(fileHandle) + bcolors.ENDC )
		pass

	def dumpToFile(self,fileHandle):
		logger = logging.getLogger(__name__)
		try:
			with open(fileHandle,'w') as dataFile:
				tempJSON = copy.deepcopy(self.state)
				del tempJSON[LocalState.KEY_MISSED_DEADLINES]
				json.dump(tempJSON,dataFile,indent=4)
		except Exception as e:
			logger.error(  bcolors.FAIL + "Generic exception when dumping to %s: %s"%(fileHandle, str(e)) + bcolors.ENDC)
			return
		logger.info( bcolors.OKGREEN + "Successfully wrote to file" + bcolors.ENDC )


		pass
	def updateDeadlines(self, pid, deadlines):
		self.state[LocalState.KEY_MISSED_DEADLINES].update(pid,deadlines)
		pass

	def updateState(self, appName, modeName, execTimes, periods):
		logger = logging.getLogger(__name__)
		self.state[LocalState.KEY_APP_NAME] = appName
		self.state[LocalState.KEY_MODE] =  modeName
		self.state[LocalState.KEY_EXEC_TIME] = execTimes
		self.state[LocalState.KEY_PERIODS] = periods
		logger.debug( self )

	def clearDeadlines(self):
		self.state[LocalState.KEY_MISSED_DEADLINES].clear()
		pass

	def __repr__(self):
		# Used for interactive prompt
		return "LocalState: %s is in mode %s has %s deadlines missed.\n\tExec:%s\tPeriods%s"%\
			(
				self.state[LocalState.KEY_APP_NAME],
				self.state[LocalState.KEY_MODE],
				self.state[LocalState.KEY_MISSED_DEADLINES],
				self.state[LocalState.KEY_EXEC_TIME],
				self.state[LocalState.KEY_PERIODS]
			)

	def __str__(self):
		# Used for print
		return self.__repr__()

# ***** Catch SIGINT *****
def signal_handler_SIGINT(signal, frame):
	print('Caught SIGINT')
	sys.exit(0)

def signal_handler_SIGUSR1(signal, frame):
	global localState
	print('Caught SIGUSR1, printing localState')
	print localState
	print ""
		


if __name__ == "__main__":
	logging.basicConfig(format='\t%(relativeCreated)6d - %(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
	logger = logging.getLogger(__name__)
	print "%s executing with PID %s"%(sys.argv[0],os.getpid())

	# *** Initialization ***
	signal.signal(signal.SIGINT, signal_handler_SIGINT)
	signal.signal(signal.SIGUSR1, signal_handler_SIGUSR1)


	# Test code
	# tempState = LocalState("app", 21, [1,2],[3,4] )
	# tempState.updateDeadlines(1,2)
	# print tempState
	# print tempState.state
	# tempState.dumpToFile("testFileState")
	# exit()

	# tempState = LocalState()
	# tempState.loadFromFile("testFileState")
	# print tempState
	# exit()

	tempState = LocalState("app", 21, [1,2],[3,4] )
	print tempState.state
	print tempState
	tempState.updateDeadlines(1,2)
	print tempState.state
	print tempState
	tempState.clearDeadlines()
	print tempState.state
	print tempState
	exit()


	tempState = LocalState("app", 21, [1,2],[3,4] )
	print tempState.state
	print tempState
	tempState.missedDeadlines.update(1,2)
	print tempState.state
	print tempState
	tempState.state[LocalState.KEY_MISSED_DEADLINES].update(2,3)
	print tempState.state
	print tempState
	exit()


	tempDeadlines = MissedDeadlines()
	tempDeadlines.update(21, 1)
	print tempDeadlines.total()
	tempDeadlines.update(21, 2)
	print tempDeadlines.total()
	tempDeadlines.update(22, 2)
	print tempDeadlines.total()
	tempDeadlines.clear()
	print tempDeadlines.total()
	exit()


