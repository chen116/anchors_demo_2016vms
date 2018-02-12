#!/usr/bin/env python

"""

"""



# http://docs.openstack.org/developer/keystone/api_curl_examples.html
# http://bodenr.blogspot.com/2014/03/openstack-keystone-workflow-token.html

WATCHED_FILE = '/var/run/nova/rt_properties'


import sys
import os
import signal
import MonMonInterface
import openstackFuncs
import pyinotify
import json
import logging
import pprint
import LocalState

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
		global openStackAPI
		global processedUUIDs

		tempUUIDs = []

		logger.info( bcolors.WARNING + "Got FileClosedEvent: %s"%(event.pathname) + bcolors.ENDC )
		
		fileName = os.path.basename(event.pathname)
		# openStackAPI.UpdateTokenV3()

		try:
			with open(event.pathname) as dataFile:
				tempJSON = json.load(dataFile)
		except IOError as e:
			# No file exists
			logger.error( "IOError: " + e )
			logger.error( bcolors.FAIL + "Failed to open %s, doing nothing"%(event.pathname) + bcolors.ENDC  )
			return
		except ValueError as e:
			# Error with formatting
			logger.error( "ValueError: " + str(e) )
			logger.error( bcolors.FAIL + "Failed to open %s, doing nothing"%(event.pathname) + bcolors.ENDC )
			return

		logger.debug(bcolors.HEADER + "Known UUIDs" + bcolors.ENDC)
		logger.debug(processedUUIDs)
		logger.debug(bcolors.HEADER+"FileContents"+bcolors.ENDC)
		for line in pprint.pformat(tempJSON).splitlines():
			logger.debug("\t"+line)

		for item in tempJSON.keys():
			if item in processedUUIDs:
				logger.debug("VM already processed, skipping")
				del processedUUIDs[processedUUIDs.index(item)]
			else:
				logger.debug("VM hasn't been processed, sending sample")
				meterName = "rtOpenstack_"+item
				execTimes = tempJSON[item][0]
				periods = tempJSON[item][1]
				execTimes = map(int,execTimes)
				periods = map(int,periods)
				tempState = LocalState.LocalState(appName="VMStartup",
					modeName=1,
					execTimes=execTimes,
					periods=periods
				)
				openStackAPI.addSample(
					meter=meterName,
					value=1,
					resource_id=item,
					metaData=MonMonInterface.CeilometerSample(
						MonMonInterface.CeilometerSample.SAMPLE_TYPE_MODE_CHANGE,
						tempState).sample
					)
			tempUUIDs.append(item)
		logger.info("Following VMs no longer on node: %s"%(processedUUIDs))
		processedUUIDs = tempUUIDs

	

# ***** Catch SIGINT *****
def signal_handler_SIGINT(signal, frame):
	print('Caught SIGINT')
	sys.exit(0)

def signal_handler_SIGUSR1(signal, frame):
	global localState
	print('Caught SIGUSR1, printing localState')
	print localState
	print ""

# TODO: Maybe change hard-coded IP
openStackAPI = openstackFuncs.OpenStackAPI(keystone_address="172.16.91.138",ceilometer_address="172.16.91.138")

processedUUIDs = []

if __name__ == "__main__":
	logging.basicConfig(format='%(relativeCreated)6d - %(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
	logger = logging.getLogger(__name__)
	print "%s executing with PID %s"%(sys.argv[0],os.getpid())

	# *** Initialization ***
	signal.signal(signal.SIGINT, signal_handler_SIGINT)
	signal.signal(signal.SIGUSR1, signal_handler_SIGUSR1)

	# Setup notifier for files
	wm = pyinotify.WatchManager()  # Watch Manager
	mask = pyinotify.IN_CLOSE_WRITE
	handler = EventHandler()
	notifier = pyinotify.Notifier(wm, handler)
	wdd = wm.add_watch(WATCHED_FILE, mask, rec=True)

	notifier.loop()	# Starts the notifier wait loop




