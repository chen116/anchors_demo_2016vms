#!/usr/bin/env python

import sys
import requests
import os
import json
import subprocess
import logging



'''
def mkdir_p(path):

def __init__(self, keystone_address=None, username=None, password=None, project=None, 
		ceilometer_address= None,nova_address=None,token=None,project_id=None):
	
	Constructor

	keystone_address		Address of keystone server
	username				Keystone username
	password				Keystone password
	project 				Project
	ceilometer_address		Address of ceilometer server
	nova_address			Address of nova-conductor server
	token 					Authentication token
	project_id 				Project id

	Any parameters not passed are initialized to defaults


def UpdateTokenV3(self,
	keystone_address = None, 
	username = None,
	password = None,
	project = None):

	Get a new authentication token and project_id.
	Returns:	None on failure, prints error

	keystone_address		Address of keystone server
	username				Keystone username
	password				Keystone password
	project 				Project

	Any parameters not passed use defaults


def getSamples(self,  meter, ceilometer_address=None,token=None):
	meter					Meter to get samples from
	ceilometer_address		Address of ceilometer server
	token 					Authentication token

	Get JSON formatted list of samples from meter
	Returns:	None on failure, prints error

	Any parameters not passed use defaults


def getLastSample(self, meter, ceilometer_address=None, token=None):
	meter					Meter to get samples from
	ceilometer_address		Address of ceilometer server
	token 					Authentication token

	Get JSON formatted last sample from meter
	Returns:	None on failure, prints error

	Any parameters not passed use defaults


def addSample(self, meter, value, resource_id, token=None, ceilometer_address=None,unit="%", metaData=None):
	meter					Meter to add samples to
	value					Value for sample
	token 					Authentication token
	ceilometer_address		Address of ceilometer server
	unit					Unit for sample
	metaData				Optional metadata to add to sample

	Add a sample to the meter
	Returns:	None on failure, prints error


def clearSamples(self, meter, ceilometer_address=None):
	meter					Meter to add samples to
	ceilometer_address		Address of ceilometer server

	Clear the samples from meter. Does not remove meter name from list of meters

	Caveat: only works when address is localhost


def alarmIDtoName(self, alarm_id, ceilometer_address=None, token=None):
	alarm_id				UUID of alarm to find name for
	ceilometer_address		Address of ceilometer server
	token 					Authentication token

	Gets the real name of the alarm with ID UUID
	Returns:	None on failure, prints error


def getXenVMList(self):
	Get list of names of running Xen VMs


def changeRTParam(self, name, budget, period, vcpu = None):
	name 					Name of VM to change parameters
	budget					Budget (ms)
	period					Period (ms)
	vcpu 					Which VCPU to change

	Change RT parameters for given VM
	Returns:	None on failure, prints error


def getXenNumVCPUs(self, name):
	name 					Name of VM to get VCPUs

	Get number of VCPUs for the given VM
	Returns:	None on failure, prints error


def changeNumVCPUs(self, name, numVCPUs):
	name 					Name of VM to change VCPU count
	numVCPUs 				Number of VCPUs to assign
	Prints error on failure


def getXenNameFromUUID(self, UUID, nova_address=None, project_id=None, token=None):
	UUID 					UUID of nova instance
	nova_address			Address of nova-conductor server
	project_id				ID for nova instances
	token 					Authentication token

	Get the xen name from the nova name
	Returns:	None on failure, prints error


def getInstanceUUID(self):
	Get the UUID inside a VM
	Returns:	None on failure, prints error



'''





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

# Emulates makedir -p functionality from shell.  
# Credit: http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise


class OpenStackAPI:
	DEFAULT_USERNAME = "admin"
	DEFAULT_PASSWORD = "anch0rs"
	DEFAULT_KEYSTONE_ADDRESS = "controller"
	DEFAULT_PROJECT = "admin"
	DEFAULT_CEILOMETER_ADDRESS = "controller"
	DEFAULT_NOVA_ADDRESS = "controller"

	def __init__(self, keystone_address=None, username=None, password=None, project=None, 
		ceilometer_address= None,nova_address=None,token=None,project_id=None):
		if keystone_address == None:
			self.keystone_address = OpenStackAPI.DEFAULT_KEYSTONE_ADDRESS
		else:
			self.keystone_address = keystone_address
		if username == None:
			self.username = OpenStackAPI.DEFAULT_USERNAME
		else:
			self.username = username
		if password == None:
			self.password = OpenStackAPI.DEFAULT_PASSWORD
		else:
			self.password = password
		if project == None:
			self.project = OpenStackAPI.DEFAULT_PROJECT
		else:
			self.project = project
		if ceilometer_address == None:
			self.ceilometer_address = OpenStackAPI.DEFAULT_CEILOMETER_ADDRESS
		else:
			self.ceilometer_address = ceilometer_address
		if nova_address == None:
			self.nova_address = OpenStackAPI.DEFAULT_NOVA_ADDRESS
		else:
			self.nova_address = nova_address
		if token == None or project_id == None:
			self.token = self.UpdateTokenV3()
		else:
			self.token = token
			self.project_id = project_id

	'''*** Keystone Functions ***'''
	def UpdateTokenV3(self,
		keystone_address = None, 
		username = None,
		password = None,
		project = None):
		logger = logging.getLogger(__name__)
		logger.debug("Trying to get new token")

		if keystone_address == None:
			keystone_address = self.keystone_address
		if username == None:
			username = self.username
		if password == None:
			password = self.password
		if project == None:
			project = self.project

		url = "http://%s:5000/v3/auth/tokens"%(str(keystone_address))
		headers = {'Content-Type': 'application/json', 
			'Accept': 'application/json'}
		payload = { "auth": {
			"identity": {
				"methods": ["password"],
				"password": {
					"user": {
						"name": str(username),
						"domain": { "id": "default" },
						"password": str(password)
					}
				}
			}
		} }

		if project != None:
			payload["auth"]["scope"] = \
				{
					"project": {
						"name": str(project),
						"domain": { "id": "default" }
						}
				}

		try:
			r = requests.post(url,data=json.dumps(payload), headers=headers)
		except requests.exceptions.ConnectionError as e:
			logger.error( bcolors.FAIL + "Error, failed to get token %s"%(e) + bcolors.ENDC )
			return None
		if r.status_code != 201:
			# Could also r.raise_for_status()
			logger.error( bcolors.FAIL + "Error, failed to get token %s"%(r.status_code) + bcolors.ENDC )
			return None
		self.token = r.headers['x-subject-token']
		self.project_id = r.json()["token"]["project"]["id"]
		# print r.text
		logger.debug("Got new token")
		return self.token

	'''*** Ceilometer Functions ***'''
	def getSamples(self,  meter, ceilometer_address=None,token=None):
		logger = logging.getLogger(__name__)
		if ceilometer_address == None:
			ceilometer_address = self.ceilometer_address
		if token == None:
			token = self.token
		
		url = "http://%s:8777/v2/meters/"%(str(ceilometer_address))
		url = url+str(meter)
		# print url
		headers = {
			'Content-Type': 'application/json', 
			'Accept': 'application/json', 
			'X-Auth-Token':str(token) }
		r = requests.get(url,headers=headers)

		if r.status_code != 200:
			logger.error( bcolors.FAIL + "Error, failed to get meters %s"%(r.status_code) + bcolors.ENDC )
			return None
		return r.json()

	def getLastSample(self, meter, ceilometer_address=None, token=None):
		temp = self.getSamples(meter, ceilometer_address = ceilometer_address, token=token)
		if temp == None or not len(temp):
			return None
		return temp[0]

	def addSample(self, meter, value, resource_id, token=None, ceilometer_address=None,unit="%", metaData=None):
		logger = logging.getLogger(__name__)
		if token == None:
			token = self.token
		if ceilometer_address == None:
			ceilometer_address = self.ceilometer_address

		url = "http://%s:8777/v2/meters/"%(str(ceilometer_address))
		url = url + str(meter)
		headers = {'Content-Type': 'application/json',
					'X-Auth-Token':str(token)}
		payload = [
			   {
				 "counter_name": str(meter),
				 "resource_id": str(resource_id),
				 "counter_unit": str(unit),
				 "counter_volume": value,
				 "counter_type": "gauge"
			   }
			 ]
		if metaData != None:
			payload[0]['resource_metadata'] = metaData
		else:
			payload[0]['resource_metadata'] = {}
		r = requests.post(url,data=json.dumps(payload),headers=headers)
		if r.status_code != 201:
			logger.error( bcolors.FAIL + "Error adding sample: %s"%(r.status_code) + bcolors.ENDC )

	# Caveat: Only works when ceilometer_address is localhost
	def clearSamples(self, meter, ceilometer_address=None):
		if ceilometer_address == None:
			ceilometer_address = self.ceilometer_address
		command = "db.meter.remove({counter_name: '%s'})"% str(meter)
		subprocess.call(["mongo", "-host", str(ceilometer_address), 
			"--eval", command, 
			"ceilometer"])

	def alarmIDtoName(self, alarm_id, ceilometer_address=None, token=None):
		logger = logging.getLogger(__name__)
		if ceilometer_address == None:
			ceilometer_address = self.ceilometer_address
		if token == None:
			token = self.token
		url = "http://%s:8777/v2/alarms/"%(str(ceilometer_address))
		headers = {
			'Content-Type': 'application/json', 
			'Accept': 'application/json', 
			'X-Auth-Token':str(token) }
		r = requests.get(url,headers=headers)
		if r.status_code != 200:
			logger.error( bcolors.FAIL + "Error getting alarm name: %s"%(r.status_code) + bcolors.ENDC )
			return None
		for alarm in r.json():
			if alarm['alarm_id']== alarm_id:
				return alarm['name']
		logger.error( bcolors.FAIL + "Alarm not found" + bcolors.ENDC )
		return None

	def getXenVMList(self):
		logger = logging.getLogger(__name__)
		vmList = []
		lines = subprocess.check_output(["xl","list"]).split('\n')
		if not len(lines):
			logger.error( bcolors.FAIL + "No VMs" + bcolors.ENDC )
		del(lines[0])
		del(lines[len(lines)-1])
		for line in lines:
			vmList.append(line.split()[0])
		return vmList

	def changeRTParam(self, name, budget, period, vcpu = None):
		logger = logging.getLogger(__name__)
		if name in self.getXenVMList():
			if vcpu is None:
				logger.error( bcolors.FAIL + 'Warning: This is supposed to be deprecated' + bcolors.ENDC )
				subprocess.call(["xl","sched-rtds","-d",str(name),
					"-b", str(budget), "-p", str(period)])
			else:
				subprocess.call(["xl","sched-rtds","-d",str(name),
					"-b", str(budget), "-p", str(period), "-v", str(vcpu)])
			return
		logger.error( bcolors.FAIL + "Error: VM not powered on" + bcolors.ENDC )

	def getXenNumVCPUs(self, name):
		logger = logging.getLogger(__name__)
		lines = subprocess.check_output(["xl","list"]).split('\n')
		for line in lines:
			splitLine = line.split()
			if splitLine[0] == name:
				return int(splitLine[3])
		logger.error( bcolors.FAIL + "Error: VM not powered on" + bcolors.ENDC )
		return None

	def changeNumVCPUs(self, name, numVCPUs):
		logger = logging.getLogger(__name__)
		if self.getXenNumVCPUs(name) == int(numVCPUs):
			return
		if ( subprocess.call(["xl","vcpu-set",name,str(numVCPUs)]) ) != 0:
			logger.error( bcolors.FAIL + "Error, changing VCPU count failed!!!" + bcolors.ENDC )

	'''*** Nova Functions ***'''
	def getXenNameFromUUID(self, UUID, nova_address=None, project_id=None, token=None):
		logger = logging.getLogger(__name__)
		if nova_address == None:
			nova_address = self.nova_address
		if project_id == None:
			project_id = self.project_id
		if token == None:
			token = self.token
		url = "http://%s:8774/v2/%s/servers/%s"%\
			(str(nova_address),str(project_id),str(UUID))
		headers = {'Content-Type': 'application/json', 
					'Accept': 'application/json',
					'X-Auth-Token': str(token)}
		
		r = requests.get(url,headers=headers)
		if r.status_code != 200:
			logger.error( bcolors.FAIL + "Error getting Xen Name: %s"%(r.status_code) + bcolors.ENDC )
			return None
		
		try:
			xenName = r.json()['server']['OS-EXT-SRV-ATTR:instance_name']
		except KeyError,e:
			logger.error( "Got KeyError" )
			logger.error( "\t"+str(e) )
			return None
		return xenName

	'''*** Metadata Functions ***'''
	def getInstanceUUID(self):
		logger = logging.getLogger(__name__)
		url = 'http://169.254.169.254/openstack/latest/meta_data.json'
		try:
			r = requests.get(url,timeout=5)
		except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
			logger.error( bcolors.FAIL + "Error, connection timed out when getting UUID" + bcolors.ENDC )
			return None

		if "uuid" in r.json():
			return r.json()['uuid']
		logger.error( bcolors.FAIL + "Error, UUID not in response" + bcolors.ENDC )
		return None


	'''*** Etc Functions ***'''
	def __repr__(self):		# Used for interactive prompt
		return "Addresses: \nKeystone: %s\tCeilometer: %s\tNova: %s\nProject: %s\tToken: %s\nProjectID: %s\nUser: %s\t Password: %s\n"%(
			self.keystone_address,
			self.ceilometer_address,
			self.nova_address,
			self.project,
			self.token,
			self.project_id,
			self.username,
			self.password)
	def __str__(self):		# Used for print
		return self.__repr__()	




if __name__ == "__main__":
	logging.basicConfig(format='\t%(relativeCreated)6d - %(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
	logger = logging.getLogger(__name__)
	print "%s executing with PID %s"%(sys.argv[0],os.getpid())

	myAPI = OpenStackAPI(keystone_address = "172.16.91.138",
		ceilometer_address = "172.16.91.138",
		nova_address = "172.16.91.138",
		token = "da4158cde3f1491785fdaeafcc6ed5ac",
		project_id = "b8d14fac00f8484a98b5439e84f11d67")
	print myAPI

	from pprint import pprint
	# pprint(myAPI.getSamples("vcpus"))
	# pprint(myAPI.getSamples("vcpus1"))

	# pprint(myAPI.getLastSample("vcpus"))
	# pprint(myAPI.getLastSample("vcpus1"))

	# print "Testing addSample"
	# print "Current"
	# pprint(myAPI.getSamples("vTest"))
	# myAPI.addSample(meter = "vTest", value = 1, resource_id = 21)
	# myAPI.addSample("vTest", 2, 21)
	# print "After add"
	# pprint(myAPI.getSamples("vTest"))
	# myAPI.clearSamples("vTest","controller")

	# def getXenNameFromUUID(self, UUID, nova_address=None, project_id=None, token=None):
	# print myAPI.getXenNameFromUUID("74a3ed32-4ea8-44ca-9fd7-6aadf760c262")
	# print myAPI.getInstanceUUID()

	# print myAPI.alarmIDtoName("707f143d-a274-4838-b8e2-c24adb26baa1")
	# print myAPI.getXenVMList()
	# myAPI.changeRTParam(name="instance-00000010", budget=10000, period=10000, vcpu = all)
	# print myAPI.getXenNumVCPUs(name="instance-00000010")
	# myAPI.changeNumVCPUs(name="instance-00000010",numVCPUs=2)
	# print myAPI.getXenNumVCPUs(name="instance-00000010")

