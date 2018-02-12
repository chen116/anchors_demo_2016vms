#!/usr/bin/env python
"""
Very simple HTTP server in python.
https://gist.github.com/bradmontgomery/2219997
Usage::
	./dummy-web-server.py [<port>]
Send a GET request::
	curl http://localhost
Send a HEAD request::
	curl -I http://localhost
Send a POST request::
	curl -d "foo=bar&bin=baz" http://localhost
"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json
import openstackFuncs
import logging
import MonMonInterface
import HostState
import CartsFuncs
import pprint
import signal
import threading
import sys

STATE_FILE = '/root/rtOpenstack/hostMonitorTest'
CARTS_INPUT_FILE = '/root/rtOpenstack/cartsTmp/hostMonCartsInput.xml'
CARTS_OUTPUT_FILE = '/root/rtOpenstack/cartsTmp/hostMonCartsOutput.xml'
RENEW_TOKEN_PERIOD = 1800

currentTimer = threading.Timer(RENEW_TOKEN_PERIOD,None)

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

def updateKeystoneToken():
	global openStackAPI
	global currentTimer
	logger.info(bcolors.HEADER + "Updating admin token" + bcolors.ENDC)
	openStackAPI.UpdateTokenV3()
	# Start next timer
	currentTimer = threading.Timer(RENEW_TOKEN_PERIOD,updateKeystoneToken)
	currentTimer.start()

# ***** Catch SIGINT *****
def signal_handler_SIGINT(signal, frame):
	global currentTimer
	print('Caught SIGINT')
	print('Killing timer')
	currentTimer.cancel()
	sys.exit(0)

class S(BaseHTTPRequestHandler):
	def _set_headers(self):
		# print 'setting headers'
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()

	def do_GET(self):
		print 'start get'
		self._set_headers()
		# This is written back to the client
		self.wfile.write("<html><body><h1>hi!</h1></body></html>")

	def do_HEAD(self):
		print 'start head'
		self._set_headers()
		
	def do_POST(self):
		global openStackAPI
		global hostState
		logger.info( bcolors.OKBLUE + 'start post' + bcolors.ENDC)
		valuesUpdated = False

		# Update admin token
		# TODO: Possibly change this to periodic to not slow down POST
		# openStackAPI.UpdateTokenV3()

		logger.debug(bcolors.HEADER + "Admin Token: " + bcolors.ENDC + openStackAPI.token)

		length = int(self.headers.getheader('content-length'))
		# logger.debug( self.rfile.read(length) )
		postData = self.rfile.read(length)
		logger.debug(bcolors.HEADER + "Posted Data:" + bcolors.ENDC)
		tempData = postData.splitlines()
		for line in tempData:
			logger.debug("\t" + line)
		logger.debug(bcolors.HEADER + "End Posted Data:" + bcolors.ENDC)
		try:
			postData = json.loads(postData)
		except ValueError as e:
			logger.error( "ValueError: " + str(e) )
			logger.error( bcolors.FAIL + "Failed to process alarm data\n" + bcolors.ENDC )
			self._set_headers()
			self.wfile.write("<html><body><h1>POST!</h1></body></html>")
			return

		#  Convert alarmID to Name
		logger.debug(bcolors.OKBLUE + "Trying to parse alarm alert" + bcolors.ENDC)
		try:
			alarmID = postData["alarm_id"]
			alarmName = postData["alarm_name"]
			meterName = alarmName
			vmUUID = alarmName.split('_',1)[1]
		except KeyError as e:
			logger.error( "KeyError: " + str(e) )
			logger.error( bcolors.FAIL + "Bad post data, not a valid alert\n" + bcolors.ENDC )
			self._set_headers()
			self.wfile.write("<html><body><h1>POST!</h1></body></html>")
			return
		logger.debug(bcolors.OKGREEN + "Success parsing alarm alert" + bcolors.ENDC)

		# Get last sample
		logger.debug(bcolors.OKBLUE + "Trying to get last sample" + bcolors.ENDC)
		lastSample = openStackAPI.getLastSample(meter=alarmName)
		if lastSample == None:
			logger.debug(bcolors.FAIL + "Failed to get last sample\n" + bcolors.ENDC)
			self._set_headers()
			self.wfile.write("<html><body><h1>POST!</h1></body></html>")
			return
		logger.debug(bcolors.OKGREEN + "Success getting last sample" + bcolors.ENDC)
		logger.debug(bcolors.HEADER + "Last sample: " + bcolors.ENDC)
		for line in pprint.pformat(lastSample).splitlines():
			logger.debug("\t"+line)

		# Extract metadata from sample
		sampleMetadata = lastSample["resource_metadata"]
		payloadType = sampleMetadata[MonMonInterface.CeilometerSample.SAMPLE_TYPE_KEY]
		samplePayload = json.loads(sampleMetadata[MonMonInterface.CeilometerSample.SAMPLE_PAYLOAD_KEY])

		# Update the state
		logger.info("Attempting to process payload and update state for %s"%(vmUUID))
		if payloadType == MonMonInterface.CeilometerSample.SAMPLE_TYPE_DEADLINE_MISS:
			logger.info(bcolors.HEADER + "Got deadline miss payload" + bcolors.ENDC)
			newDeadlinesMissed = samplePayload[MonMonInterface.CeilometerSample.KEY_PAYLOAD_MISS]
			if vmUUID not in hostState.vmList():
				valuesUpdated = True
			else:
				oldDeadlinesMissed = hostState.entries()[vmUUID][HostState.HostState.KEY_DEADLINES]
				if oldDeadlinesMissed != newDeadlinesMissed:
					valuesUpdated = True
			hostState.updateVM(vmUUID=vmUUID,
				deadlinesMissed=newDeadlinesMissed)
		elif payloadType == MonMonInterface.CeilometerSample.SAMPLE_TYPE_MODE_CHANGE:
			logger.info(bcolors.HEADER + "Got mode change payload" + bcolors.ENDC)
			newMode = samplePayload[MonMonInterface.CeilometerSample.KEY_PAYLOAD_MODE]
			newAppParams = [ samplePayload[MonMonInterface.CeilometerSample.KEY_PAYLOD_EXEC_TIME],
							samplePayload[MonMonInterface.CeilometerSample.KEY_PAYLOAD_PERIOD] ]
			if vmUUID not in hostState.vmList():
				valuesUpdated = True
			else:
				oldMode = hostState.entries()[vmUUID][HostState.HostState.KEY_APP_MODE]
				oldAppParams = hostState.entries()[vmUUID][HostState.HostState.KEY_APP_PARAMS]
				if oldMode != newMode or oldAppParams != newAppParams:
					valuesUpdated = True
			hostState.updateVM(vmUUID=vmUUID,
				appName=samplePayload[MonMonInterface.CeilometerSample.KEY_PAYLOAD_APP_NAME],
				mode=newMode,
				appParams=newAppParams
				)
		elif payloadType == MonMonInterface.CeilometerSample.SAMPLE_TYPE_PERIODIC_REPORT:
			logger.info(bcolors.HEADER + "Got periodic report payload" + bcolors.ENDC)
			logger.info("Not implemented, ignoring")
			self._set_headers()
			self.wfile.write("<html><body><h1>POST!</h1></body></html>")
			return			
		else:
			logger.debug(bcolors.FAIL + "Invalid sample payload type %s\n"%(payloadType) + bcolors.ENDC)
			self._set_headers()
			self.wfile.write("<html><body><h1>POST!</h1></body></html>")
			return

		if valuesUpdated == True:
			logger.info(bcolors.HEADER + "Values updated, need to process" + bcolors.ENDC)
			# Call carts with new state
			CartsFuncs.runCARTS(hostState, CARTS_INPUT_FILE, CARTS_OUTPUT_FILE)
			hostState.updateVCPUFromCARTS(CartsFuncs.readCARTSOutput(CARTS_OUTPUT_FILE))

			# Update parameters
			for key,value in hostState.entries().iteritems():
				logging.debug( "Checking params for %s"%(key) )

				vmName = openStackAPI.getXenNameFromUUID(key)
				vcpuInfo = value[HostState.HostState.KEY_VCPU_INFO]
				curNumVCPUs = 0
				curNumVCPUs = openStackAPI.getXenNumVCPUs(name=vmName)
				newNumVCPUs = len(vcpuInfo[0])
				if curNumVCPUs != newNumVCPUs:
					logging.debug( "Need to change VCPU num from %d to %d"%(curNumVCPUs, newNumVCPUs) )
					openStackAPI.changeNumVCPUs(name=vmName,numVCPUs=newNumVCPUs)

				for index in range(0,newNumVCPUs):
					budget= vcpuInfo[0][index]
					period = vcpuInfo[1][index]
					logging.debug( "Updating VCPU: %d\tbudget: %d\tperiod: %d"%(index,budget,period) )
					openStackAPI.changeRTParam(name=vmName, 
						budget=budget,
						period=period, 
						vcpu = index)
		else:
			logger.info(bcolors.HEADER + "Values didn't change, skipping" + bcolors.ENDC)

		self._set_headers()
		self.wfile.write("<html><body><h1>POST!</h1></body></html>")

		# Write back to file
		hostState.dumpToFile(STATE_FILE)

		logger.debug(bcolors.HEADER + "Current local state:" + bcolors.ENDC)
		for line in hostState.__str__().splitlines():
			logger.debug("\t"+line)
		
		logger.info( bcolors.OKGREEN + 'end post\n' + bcolors.ENDC)

	def log_message(self, format, *args):
		return
		
def run(server_class=HTTPServer, handler_class=S, port=80):
	server_address = ('', port)
	httpd = server_class(server_address, handler_class)
	print 'Starting httpd...'
	httpd.serve_forever()

# TODO: Maybe change hard-coded IP
openStackAPI = openstackFuncs.OpenStackAPI(keystone_address="172.16.91.138",ceilometer_address="172.16.91.138")
hostState = HostState.HostState()


if __name__ == "__main__":
	logging.basicConfig(format='%(relativeCreated)6d - %(asctime)s - %(name)20s - %(levelname)7s - %(message)s',
		level=logging.DEBUG)
	logger = logging.getLogger(__name__)
	logging.getLogger("requests").setLevel(logging.WARNING)
	from sys import argv
	signal.signal(signal.SIGINT, signal_handler_SIGINT)

	updateKeystoneToken()
	hostState.loadFromFile(STATE_FILE)

	if len(argv) == 2:
		run(port=int(argv[1]))
	else:
		run()

