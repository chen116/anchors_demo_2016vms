#!/usr/bin/env python
"""

"""

import logging
import pprint
import json
# import openstackFuncs
# import MonMonInterface

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

class HostState:
	'''
		self.state: 
		{
			vmUUID: 
				{
					"VCPUs":
					[
						[budgets],
						[periods],
						[deadlines]
					],
					"ApplicationName": STR,
					"CurrentMode": INT,
					"DeadlinesMissed": INT,
					"ApplicationParams":
					[
						[exec times],
						[periods]
					]
				},
			...
		}
	'''
	KEY_VCPU_INFO = "VCPUs"
	KEY_APP_NAME = "ApplicationName"
	KEY_APP_MODE = "CurrentMode"
	KEY_DEADLINES = "DeadlinesMissed"
	KEY_APP_PARAMS = "ApplicationParams"

	def __init__(self):
		logger = logging.getLogger(HostState.__init__.__name__)
		logger.debug(bcolors.OKBLUE + "Initialize HostState" + bcolors.ENDC)
		self.state = {}
		pass

	'''
	vmUUID 				String
	appName 			String
	mode 				Int
	deadlinesMissed 	Int
	appParams 			list(execTimes, periods)
	'''
	def updateVM(self, vmUUID, vcpuInfo=None, appName=None, mode=None, deadlinesMissed=None, appParams=None):
		logger = logging.getLogger(HostState.updateVM.__name__)
		logger.debug(bcolors.OKBLUE + "Update HostState" + bcolors.ENDC)

		vmEntry = {}
		if vmUUID in self.state.keys():
			logger.debug("VM exists in local state")
			oldVMEntry = self.state[vmUUID]
			if vcpuInfo == None:
				vcpuInfo = oldVMEntry[HostState.KEY_VCPU_INFO]
			if appName == None:
				appName = oldVMEntry[HostState.KEY_APP_NAME]
			if mode == None:
				mode = oldVMEntry[HostState.KEY_APP_MODE]
			if deadlinesMissed == None:
				deadlinesMissed = oldVMEntry[HostState.KEY_DEADLINES]
			if appParams == None:
				appParams = oldVMEntry[HostState.KEY_APP_PARAMS]
		else:
			logger.debug("VM not found, new entry")
			deadlinesMissed = 0
			vcpuInfo = [[],[]]
			if appName == None or mode == None or appParams == None:
				logger.error(bcolors.FAIL + "On first update, must include mode, name, and params!" + bcolors.ENDC)
				return

		vmEntry[HostState.KEY_VCPU_INFO] = vcpuInfo
		vmEntry[HostState.KEY_APP_NAME] = appName
		vmEntry[HostState.KEY_APP_MODE] = mode
		vmEntry[HostState.KEY_DEADLINES]	= deadlinesMissed
		vmEntry[HostState.KEY_APP_PARAMS] = appParams

		self.state[vmUUID] = vmEntry
		pass

	def updateVCPUFromCARTS(self, cartsOutput):
		logger = logging.getLogger(HostState.updateVCPUFromCARTS.__name__)
		logger.debug(bcolors.OKBLUE + "Updating HostState from CARTS" + bcolors.ENDC)

		# pprint.pprint( self.state )
		for key,value in cartsOutput.iteritems():
			self.state[key][HostState.KEY_VCPU_INFO] = value
		# pprint.pprint( self.state)
		logger.debug(bcolors.OKGREEN + "Done updating HostState from CARTS" + bcolors.ENDC)
		pass

	def entry(self, vmUUID):
		logger = logging.getLogger(HostState.entry.__name__)
		if vmUUID in self.state.keys():
			logger.debug("VM found")
			return self.state[vmUUID]
		else:
			logger.error( bcolors.FAIL + "VM not in entries" + bcolors.ENDC )
			return None

	def entries(self):
		return self.state

	def vmList(self):
		return self.state.keys()

	def loadFromFile(self,fileHandle):
		logger = logging.getLogger(HostState.loadFromFile.__name__)
		try:
			with open(fileHandle) as dataFile:
				self.state = json.load(dataFile)

			logger.info(bcolors.OKGREEN + "Successfully loaded from file" + bcolors.ENDC)
		except IOError as e:
			# No file exists
			logger.error( "IOError: " + str(e) )
			logger.error( bcolors.FAIL + "Failed to open %s, not loading"%(fileHandle) + bcolors.ENDC )
		except ValueError as e:
			# Error with formatting
			logger.error( "ValueError: " + str(e) )
			logger.error( bcolors.FAIL + "Failed to open %s, not loading"%(fileHandle) + bcolors.ENDC )

	def dumpToFile(self,fileHandle):
		logger = logging.getLogger(HostState.dumpToFile.__name__)
		try:
			with open(fileHandle,'w') as dataFile:
				json.dump(self.state,dataFile,indent=4)
		except Exception as e:
			logger.error(  bcolors.FAIL + "Generic exception when dumping to %s: %s"%(fileHandle, str(e)) + bcolors.ENDC)
			return
		logger.info( bcolors.OKGREEN + "Successfully wrote to file" + bcolors.ENDC )

	def __repr__(self):
		# Used for interactive prompt
		logger = logging.getLogger(HostState.__repr__.__name__)
		return pprint.pformat(self.state)
		# return str(self.state)

	def __str__(self):
		# Used for print
		return self.__repr__()


if __name__ == "__main__":
	logging.basicConfig(format='\t%(relativeCreated)6d - %(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
	logger = logging.getLogger(__name__)

	print bcolors.HEADER + "Blank init" + bcolors.ENDC
	tempHost = HostState()
	print tempHost

	print bcolors.HEADER + "Update newVM" + bcolors.ENDC
	tempHost.updateVM(vmUUID="TestHost", vcpuInfo = [[1,2],[3,4]], appName="TestApp", mode = 5, deadlinesMissed=25, appParams=[[5,6],[7,8]])
	print tempHost

	print bcolors.HEADER + "Update same VM" + bcolors.ENDC
	tempHost.updateVM(vmUUID="TestHost", vcpuInfo = [[11,21],[31,41]], appName="TestApp1", mode = 51, deadlinesMissed=251, appParams=[[51,61],[71,81]])
	print tempHost

	print bcolors.HEADER + "Update another new VM" + bcolors.ENDC
	tempHost.updateVM(vmUUID="TestHost2", vcpuInfo = [[12,22],[32,42]], appName="TestApp2", mode = 52, deadlinesMissed=252, appParams=[[52,62],[72,82]])
	print tempHost

	print bcolors.HEADER + "Get entry" + bcolors.ENDC
	print tempHost.entry("TestHost")

	print bcolors.HEADER + "Get non-existant entry" + bcolors.ENDC
	print tempHost.entry("TestHost24")

	print bcolors.HEADER + "Get entries" + bcolors.ENDC
	print tempHost.entries()

	print bcolors.HEADER + "Dumping to file" + bcolors.ENDC
	tempHost.dumpToFile('/Users/Geoffrey/Desktop/TestFiles/hostState/sampleHostStateDumped')

	print bcolors.HEADER + "Loading from file" + bcolors.ENDC
	tempHost.loadFromFile('/Users/Geoffrey/Desktop/TestFiles/hostState/sampleHostStateLoad')
	print tempHost



