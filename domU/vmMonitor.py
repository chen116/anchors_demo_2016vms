#!/usr/bin/env python

"""
Watch the directory for any file changes
Depending on file name, we know if it is a mode change or missed deadlines
/dev/shm/vmMon/mode	- mode change information
/dev/shm/vmMon/$PID - missed deadline
"""

# NOTE: Possibly make this threaded? Would need locks on LocalState/MissedDeadlines


# TODO: Update keystone token periodically?  
# http://docs.openstack.org/developer/keystone/api_curl_examples.html
# http://bodenr.blogspot.com/2014/03/openstack-keystone-workflow-token.html

WATCHED_DIR = "/dev/shm/rtOpenstack/"
STATE_FILE = "/root/vmMonState"

FILE_NAME_MODE_CHANGE = "mode"
APP_INTERFACE_DEADLINE_KEY = "DeadlinesMissed"
APP_INTERFACE_APPLICATION_KEY = "Application name"
APP_INTERFACE_MODE_KEY = "Mode name"
APP_INTERFACE_PERIOD_KEY = "Periods"
APP_INTERFACE_EXEC_KEY = "ExecTime"

import sys
import os
import inspect
import signal
import MonMonInterface
import openstackFuncs
import pyinotify
import json
import logging
from LocalState import LocalState

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

class EventHandler(pyinotify.ProcessEvent):
	def process_IN_CLOSE_WRITE(self, event):
		global localState
		global openStackAPI
		global vmUUID
		global meterName
		logger.info( bcolors.WARNING + "%s Got FileClosedEvent: %s"%(vmUUID, event.pathname) + bcolors.ENDC )
		
		fileName = os.path.basename(event.pathname)
		openStackAPI.UpdateTokenV3()

		try:
			with open(event.pathname) as dataFile:
				tempJSON = json.load(dataFile)
		except IOError as e:
			# No file exists
			logger.error( "IOError: " + e )
			logger.error( bcolors.FAIL + "Failed to open %s, doing nothing"%(event.pathname) + bcolors.ENDC  )
		except ValueError as e:
			# Error with formatting
			logger.error( "ValueError: " + str(e) )
			logger.error( bcolors.FAIL + "Failed to open %s, doing nothing"%(event.pathname) + bcolors.ENDC )

		if fileName == FILE_NAME_MODE_CHANGE:
			logger.debug( bcolors.OKGREEN + "Mode Change Detected" + bcolors.ENDC )
			try:
				# Update local state
				localState.updateState(
					appName=tempJSON[APP_INTERFACE_APPLICATION_KEY], 
					modeName=tempJSON[APP_INTERFACE_MODE_KEY], 
					execTimes=tempJSON[APP_INTERFACE_EXEC_KEY], 
					periods=tempJSON[APP_INTERFACE_PERIOD_KEY]
					)
				openStackAPI.addSample(
					meter=meterName,
					value=1,
					resource_id=vmUUID,
					metaData=MonMonInterface.CeilometerSample(
						MonMonInterface.CeilometerSample.SAMPLE_TYPE_MODE_CHANGE,
						localState).sample
					)
				pass
			except KeyError as e:
				logger.error( bcolors.FAIL + "App interface failed, no %s in mode file"%(e) + bcolors.ENDC )

		else:
			logger.debug( bcolors.OKGREEN + "Deadlines Reported" + bcolors.ENDC )
			try:
				localState.updateDeadlines(fileName, tempJSON[APP_INTERFACE_DEADLINE_KEY])
				openStackAPI.addSample(
					meter=meterName,
					value=1,
					resource_id=vmUUID,
					metaData=MonMonInterface.CeilometerSample(
						MonMonInterface.CeilometerSample.SAMPLE_TYPE_DEADLINE_MISS,
						localState).sample
					)
			except KeyError as e:
				logger.error( bcolors.FAIL + "App interface failed, no %s in deadline file"%(e) + bcolors.ENDC )
		localState.dumpToFile(STATE_FILE)
		logger.info( bcolors.WARNING + "%s Done processing event %s"%(vmUUID, event.pathname) + bcolors.ENDC )



# ***** Catch SIGINT *****
def signal_handler_SIGINT(signal, frame):
	print('Caught SIGINT')
	sys.exit(0)

def signal_handler_SIGUSR1(signal, frame):
	global localState
	print('Caught SIGUSR1, printing localState')
	print localState
	print ""
		


localState = LocalState(appName = None, modeName = None, execTimes = None, periods = None)
# Try to load from file:
localState.loadFromFile(STATE_FILE)
print localState

# TODO: Maybe change hard-coded IP
openStackAPI = openstackFuncs.OpenStackAPI(keystone_address="172.16.91.138",ceilometer_address="172.16.91.138")

vmUUID = openStackAPI.getInstanceUUID()
meterName = "rtOpenstack_"+vmUUID

# openStackAPI.addSample(self, meter, value, resource_id, token=None, ceilometer_address=None,unit="%", metaData=None)
# openStackAPI.getInstanceUUID()

if __name__ == "__main__":
	logging.basicConfig(format='\t%(relativeCreated)6d - %(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
	logger = logging.getLogger(__name__)
	print "%s executing with PID %s"%(sys.argv[0],os.getpid())

	# *** Initialization ***
	signal.signal(signal.SIGINT, signal_handler_SIGINT)
	signal.signal(signal.SIGUSR1, signal_handler_SIGUSR1)

	try:
		if not os.path.exists(WATCHED_DIR):
			os.makedirs(WATCHED_DIR)
			os.chmod(WATCHED_DIR,0777)
			print "Directory %s doesn't exist! Created directory"%(WATCHED_DIR)
	except Exception as e:
		print e
		print "Line %s Quiting..."%(inspect.currentframe().f_lineno)
		exit()

	# Setup notifier for files
	wm = pyinotify.WatchManager()  # Watch Manager
	mask = pyinotify.IN_CLOSE_WRITE
	handler = EventHandler()
	notifier = pyinotify.Notifier(wm, handler)
	wdd = wm.add_watch(WATCHED_DIR, mask, rec=True)

	notifier.loop()	# Starts the notifier wait loop

	





	# Test code
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


