#!/usr/bin/env python

"""

"""

import sys
import os
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


class CeilometerSample:
	SAMPLE_TYPE_DEADLINE_MISS = "DeadlineMiss"
	SAMPLE_TYPE_MODE_CHANGE = "ModeChange"
	SAMPLE_TYPE_PERIODIC_REPORT = "PeriodicReport"

	SAMPLE_TYPE_KEY = "type"
	SAMPLE_PAYLOAD_KEY = "payload"
	KEY_PAYLOAD_MISS = "numberMissed"
	KEY_PAYLOAD_MODE = "ModeName"
	KEY_PAYLOAD_PERIOD = "Periods"
	KEY_PAYLOD_EXEC_TIME = "ExecTimes"
	KEY_PAYLOAD_APP_NAME = "AppName"

	def __init__(self, sampleType=None, localState=None):
		logger = logging.getLogger(__name__)
		if sampleType == None or localState == None:
			logger.error( bcolors.FAIL + "Failed to create sample" + bcolors.ENDC )
			return
		self.sample = {}
		if sampleType == CeilometerSample.SAMPLE_TYPE_DEADLINE_MISS:
			self.sample[CeilometerSample.SAMPLE_TYPE_KEY] = \
				CeilometerSample.SAMPLE_TYPE_DEADLINE_MISS
			self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY] = json.dumps(\
				{ 
					CeilometerSample.KEY_PAYLOAD_MISS:
						localState.state[LocalState.KEY_MISSED_DEADLINES].total()
				} )
		elif sampleType == CeilometerSample.SAMPLE_TYPE_MODE_CHANGE:
			self.sample[CeilometerSample.SAMPLE_TYPE_KEY] = \
				CeilometerSample.SAMPLE_TYPE_MODE_CHANGE
			self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY] = json.dumps(\
				{
					CeilometerSample.KEY_PAYLOAD_MODE:localState.state[LocalState.KEY_MODE],
					CeilometerSample.KEY_PAYLOAD_PERIOD:localState.state[LocalState.KEY_PERIODS],
					CeilometerSample.KEY_PAYLOD_EXEC_TIME:localState.state[LocalState.KEY_EXEC_TIME],
					CeilometerSample.KEY_PAYLOAD_APP_NAME:localState.state[LocalState.KEY_APP_NAME]
				} )
		elif sampleType == CeilometerSample.SAMPLE_TYPE_PERIODIC_REPORT:
			self.sample[CeilometerSample.SAMPLE_TYPE_KEY] = \
				CeilometerSample.SAMPLE_TYPE_PERIODIC_REPORT
			self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY] = json.dumps(\
				{
					CeilometerSample.KEY_PAYLOAD_MODE:localState.state[LocalState.KEY_MODE],
					CeilometerSample.KEY_PAYLOAD_PERIOD:localState.state[LocalState.KEY_PERIODS],
					CeilometerSample.KEY_PAYLOD_EXEC_TIME:localState.state[LocalState.KEY_EXEC_TIME],
					CeilometerSample.KEY_PAYLOAD_APP_NAME:localState.state[LocalState.KEY_APP_NAME],
					CeilometerSample.KEY_PAYLOAD_MISS:
						localState.state[LocalState.KEY_MISSED_DEADLINES].total()
				} )


	def __repr__(self):
		logger = logging.getLogger(__name__)
		# Used for interactive prompt
		tempSample = self.sample
		tempSample[CeilometerSample.SAMPLE_PAYLOAD_KEY] = json.loads(tempSample[CeilometerSample.SAMPLE_PAYLOAD_KEY])
		if self.sample[CeilometerSample.SAMPLE_TYPE_KEY] == CeilometerSample.SAMPLE_TYPE_DEADLINE_MISS:
			return "CeilometerSample: %s %s"%(self.sample[CeilometerSample.SAMPLE_TYPE_KEY],
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_MISS])
		elif self.sample[CeilometerSample.SAMPLE_TYPE_KEY] == CeilometerSample.SAMPLE_TYPE_MODE_CHANGE:
			return "CeilometerSample: %s %s:%s %s:%s\n\t%s:%s %s:%s "%(
				self.sample[CeilometerSample.SAMPLE_TYPE_KEY],
				CeilometerSample.KEY_PAYLOAD_APP_NAME,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_APP_NAME],
				CeilometerSample.KEY_PAYLOAD_MODE,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_MODE],
				CeilometerSample.KEY_PAYLOD_EXEC_TIME,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOD_EXEC_TIME],
				CeilometerSample.KEY_PAYLOAD_PERIOD,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_PERIOD]
				)
		elif self.sample[CeilometerSample.SAMPLE_TYPE_KEY] == CeilometerSample.SAMPLE_TYPE_PERIODIC_REPORT:
			return "CeilometerSample: %s %s:%s %s:%s\n\t%s:%s %s:%s %s:%s "%(
				self.sample[CeilometerSample.SAMPLE_TYPE_KEY],
				CeilometerSample.KEY_PAYLOAD_APP_NAME,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_APP_NAME],
				CeilometerSample.KEY_PAYLOAD_MODE,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_MODE],
				CeilometerSample.KEY_PAYLOD_EXEC_TIME,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOD_EXEC_TIME],
				CeilometerSample.KEY_PAYLOAD_PERIOD,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_PERIOD],
				CeilometerSample.KEY_PAYLOAD_MISS,
				self.sample[CeilometerSample.SAMPLE_PAYLOAD_KEY][CeilometerSample.KEY_PAYLOAD_MISS]
				)
		else:
			logger.error( bcolors.FAIL + "Error, invalid packet type" + bcolors.ENDC )
			return ""

	def __str__(self):
		# Used for print
		return self.__repr__()


if __name__ == "__main__":
	logging.basicConfig(format='\t%(relativeCreated)6d - %(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
	logger = logging.getLogger(__name__)
	print "%s executing with PID %s"%(sys.argv[0],os.getpid())

	testSample = CeilometerSample("send")
	testSample = CeilometerSample("receive")

	tempLocalState = LocalState("TestApplication", "TestMode", [10,10], [20,20])
	tempLocalState.updateDeadlines(21,7)
	print tempLocalState

	from pprint import pprint
	testSample = CeilometerSample(CeilometerSample.SAMPLE_TYPE_DEADLINE_MISS, tempLocalState)
	print testSample
	pprint(testSample.sample)
	testSample = CeilometerSample(CeilometerSample.SAMPLE_TYPE_MODE_CHANGE, tempLocalState)
	print testSample
	pprint(testSample.sample)
	testSample = CeilometerSample(CeilometerSample.SAMPLE_TYPE_PERIODIC_REPORT, tempLocalState)
	print testSample
	pprint(testSample.sample)

