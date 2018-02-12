#!/usr/bin/env python
"""

"""

import logging
import xml.etree.ElementTree as ET
import xml
import copy
import subprocess
import os
import HostState



CARTS_TEMPLATE_FILE = '/root/rtOpenstack/cartsTmp/openstack_multilevel_EDF.xml'
CARTS_LOCATION = '/usr/bin/Carts.jar'
CARTS_MODEL = "MPR"
CARTS_DEFAULT_INPUT = '/Users/Geoffrey/Desktop/TestFiles/cartsFuncs/testCARTSinput.xml'
CARTS_DEFAULT_OUTPUT = '/Users/Geoffrey/Desktop/TestFiles/cartsFuncs/testCARTSoutput.xml'



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


def runCARTS(hostState, inputFile=CARTS_DEFAULT_INPUT, outputFile=CARTS_DEFAULT_INPUT):
	logger = logging.getLogger(runCARTS.__name__)
	logger.debug(bcolors.OKBLUE + "runCARTS called" + bcolors.ENDC)

	logger.debug(bcolors.OKBLUE + "Generating input XML" + bcolors.ENDC)
	tree = ET.parse(CARTS_TEMPLATE_FILE)
	root = tree.getroot()

	for key,value in hostState.entries().iteritems():
		# This creates the new COMPONENT. ie, the new VM
		component = copy.deepcopy(root[0])
  		root.append(component)
  		component.attrib['name'] = key
  		component.tag = 'component'

  		budgets = value[HostState.HostState.KEY_APP_PARAMS][0]
		periods = value[HostState.HostState.KEY_APP_PARAMS][1]
		deadlines = value[HostState.HostState.KEY_APP_PARAMS][1]

		# Add the tasks for this VM
		for index2,item2 in enumerate(budgets):
			task = copy.deepcopy(component[0])
			component.append(task)
			task.attrib['p'] = str(periods[index2])
			task.attrib['d'] = str(deadlines[index2])
			task.attrib['e'] = str(budgets[index2])
			task.tag = "task"

		# Here, delete the first task, as it is the template
		component.remove(component.find('oldTask'))

	# Here, delete the first component, as it is the placeholder
	root.remove(root.find('oldComponent'))

	# print "Output tree:"
	# ET.dump(root)

	# Write to file
	try:
		tree.write(inputFile)
	except Exception as exc:
		print "Caught exception: ",exc
		"Ignoring..."
	logger.debug(bcolors.OKGREEN + "Done generating input XML" + bcolors.ENDC)


	# Actually run carts
	logger.debug(bcolors.OKBLUE + "Start running CARTS" + bcolors.ENDC)
	FNULL = open(os.devnull, 'w')
	subprocess.call([
		"java",
		"-jar",
		CARTS_LOCATION,
		inputFile,
		CARTS_MODEL, 
		outputFile
		],stderr = FNULL, stdout = FNULL)
	FNULL.close()
	os.remove('Ak_max.log')
	os.remove('run.log')
	
	logger.debug(bcolors.OKGREEN + "Done running CARTS" + bcolors.ENDC)

def readCARTSOutput(outputFile=CARTS_DEFAULT_INPUT):
	logger = logging.getLogger(readCARTSOutput.__name__)
	logger.debug(bcolors.OKBLUE + "readCARTSOutput called" + bcolors.ENDC)

	tree = ET.parse(outputFile)
	root = tree.getroot()
	VMs = root.findall('component')
	vmParamDict = {}
	for index,item in enumerate(VMs):
		# print colored('Processing %s'%item.attrib['name'],'green')
		VCPU_budgets = []
		VCPU_periods = []
		VCPU_deadlines = []
		VCPU_data = item.find('processed_task')
		for index2,item2 in enumerate(VCPU_data):
			VCPU_budgets.append(int(item2.attrib['execution_time']))
			VCPU_periods.append(int(item2.attrib['period']))
			VCPU_deadlines.append(int(item2.attrib['deadline']))
		# print VCPU_budgets,VCPU_periods,VCPU_deadlines
		vmParamDict[item.attrib["name"]]=[VCPU_budgets,VCPU_periods,VCPU_deadlines]
	return vmParamDict

if __name__ == "__main__":
	logging.basicConfig(format='\t%(relativeCreated)6d - %(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

	from pprint import pprint
	CARTS_INPUT_FILE = '/Users/Geoffrey/Desktop/TestFiles/cartsFuncs/testCARTSinput.xml'
	CARTS_OUTPUT_FILE = '/Users/Geoffrey/Desktop/TestFiles/cartsFuncs/testCARTSoutput.xml'

	'''
	Should be:
	{'TestHost': [['397'], ['400'], ['400']],
	 'TestHost2': [['400', '400', '399'],
	                                          ['400', '400', '400'],
	                                          ['400', '400', '400']]}
	'''

	tempHost = HostState.HostState()
	tempHost.updateVM(vmUUID="TestHost", 
		vcpuInfo = [[1,2],[3,4]], 
		appName="TestApp", 
		mode = 5, 
		deadlinesMissed=25, 
		appParams=[[981], [1000]])
	tempHost.updateVM(vmUUID="TestHost2", 
		vcpuInfo = [[12,22],[32,42]], 
		appName="TestApp2", 
		mode = 52, 
		deadlinesMissed=252, 
		appParams=[[998, 997], [1000, 1000]])
	print tempHost

	runCARTS(tempHost,CARTS_INPUT_FILE,CARTS_OUTPUT_FILE) 
	print "Output VCPU parameters"
	pprint(readCARTSOutput(CARTS_OUTPUT_FILE))








