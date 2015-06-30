#!/usr/bin/python

# File   : dmRecord.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Class definition for DeepMac records
# Written: 2014/02/04
# Updated: 2015/06/10

# Defines class for a DeepMac record instance, which holds the data for a DeepMac Repository
# record. Includes methods for verifying the data, getting and setting values.

import logging
import datetime
import functools
import simplejson as json

# Logging configuration
log = logging.getLogger('dm_rec')
handler = logging.StreamHandler()
logformat = logging.Formatter("%(asctime)s - %(name)s %(levelname)s: %(message)s")
handler.setFormatter(logformat)
log.addHandler(handler)
log.setLevel(logging.ERROR)

# Pull-in functools decorator for automatic ordering. This will allow sorting an array of dmRecord objects neatly.
@functools.total_ordering

####

class dmRecord:
	# Initial dictionary for holding record
	rec = {}

	# Internal constants for validating record format
	rectypes = ['registry', 'metadata']
	eventtypes = ['add', 'change', 'delete']
	ouisizes = [24, 28, 36]

	# Mapping of option keywords to record field names, used in initializing an instance
	fieldmap = {
		'rectype': 'DeepMac',
		'source': 'Source',
		'etype': 'EventType',
		'edate': 'EventDate',
		'osize': 'OUISize',
		'oui': 'OUI',
		'orgname': 'OrgName',
		'orgadd': 'OrgAddress',
		'orgcn': 'OrgCountry',
		'mac1': 'MACStart',
		'mac2': 'MACEnd',
		'conf': 'Confidence',
		'mtype': 'MediaType',
		'dtype': 'DevType',
		'dmodel': 'DevModel',
		'note': 'Note',
		'wiki': 'WikiLink'
	}

####
	
	# Function to verify we have a valid DeepMac record. Returns True if the structure
	# is an expected record type and values conform. Otherwise returns False.
	def verify(self):
		log.debug("verify() starting")

		# Look for DeepMac indicator field
		if 'DeepMac' not in self.rec:
			log.warning("Required field key 'DeepMac' missing")
			log.debug("verify() ending")
			return False
		elif self.rec['DeepMac'] not in self.rectypes:
			log.warning("Field key 'DeepMac' has illegal value")
			log.debug("verify() ending")
			return False

		# Verify common fields for all DeepMac record types
		if 'Source' not in self.rec:
			log.warning("Required field key 'Source' missing")
			log.debug("verify() ending")
			return False
		elif self.rec['Source'] == '':
			log.warning("Field key 'EventType' has illegal value (empty)")
			log.debug("verify() ending")
			return False

		if 'EventType' not in self.rec:
			log.warning("Required field key 'EventType' missing")
			log.debug("verify() ending")
			return False
		elif self.rec['EventType'] not in self.eventtypes:
			log.warning("Field key 'EventType' has illegal value")
			log.debug("verify() ending")
			return False

		if 'EventDate' not in self.rec:
			log.warning("Required field key 'EventDate' missing")
			log.debug("verify() ending")
			return False
		else:
			try:
				datetime.datetime.strptime(self.rec['EventDate'], '%Y-%m-%d')
			except ValueError:
				log.warning("Field key 'EventDate' has illegal value")
				log.debug("verify() ending")
				return False

		# Depending on record type, verify remaining possible fields
		if self.rec['DeepMac'] == 'registry':
			if 'OUISize' not in self.rec:
				log.warning("Required field key 'OUISize' missing")
				log.debug("verify() ending")
				return False
			elif self.rec['OUISize'] not in self.ouisizes:
				log.warning("Field key 'OUISize' has illegal value")
				log.debug("verify() ending")
				return False

			if 'OUI' not in self.rec:
				log.warning("Required field key 'OUI' missing")
				log.debug("verify() ending")
				return False
			if len(self.rec['OUI']) <> (self.rec['OUISize'] / 4):
				log.warning("Field key 'OUI' has illegal value (incorrect length for OUI size)")
				log.debug("verify() ending")
				return False
			elif not all(char in '0123456789ABCDEF' for char in self.rec['OUI']):
				log.warning("Field key 'OUI' has illegal value (non-HEX digits)")
				log.debug("verify() ending")
				return False

			if 'OrgName' not in self.rec:
				log.warning("Required field key 'OrgName' missing")
				log.debug("verify() ending")
				return False
			if self.rec['OrgName'] == '' :
				log.warning("Field key 'OrgName' has illegal value")
				log.debug("verify() ending")
				return False

			# Only public registry entries should have address info
			if self.rec['OrgName'] != 'PRIVATE':
				if 'OrgAddress' not in self.rec:
					log.warning("Required field key 'OrgAddress' missing")
					log.debug("verify() ending")
					return False
				if self.rec['OrgAddress'] == '':
					log.warning("Field key 'OrgAddress' has illegal value")
					log.debug("verify() ending")
					return False

				if 'OrgCountry' not in self.rec:
					log.warning("Required field key 'OrgCountry' missing")
					log.debug("verify() ending")
					return False
				if self.rec['OrgCountry'] == '':
					log.warning("Field key 'OrgCountry' has illegal value")
					log.debug("verify() ending")
					return False

			# If we reach here, it's a valid registry record
			log.debug("verify() ending")
			return True
			
		elif self.rec['DeepMac'] == 'metadata':
			if 'MACStart' not in self.rec:
				log.warning("Required field key 'MACStart' missing")
				log.debug("verify() ending")
				return False
			elif len(self.rec['MACStart']) <> 12:
				log.warning("Field key 'MACStart' has illegal value (incorrect length)")
				log.debug("verify() ending")
				return False
			elif not all(char in '0123456789ABCDEF' for char in self.rec['MACStart']):
				log.warning("Field key 'MACStart' has illegal value (invalid HEX digits)")
				log.debug("verify() ending")
				return False
			
			if 'MACEnd' not in self.rec:
				log.warning("Required field key 'MACEnd' missing")
				log.debug("verify() ending")
				return False
			elif len(self.rec['MACEnd']) <> 12:
				log.warning("Field key 'MACEnd' has illegal value")
				log.debug("verify() ending")
				return False
			elif not all(char in '0123456789ABCDEF' for char in self.rec['MACEnd']):
				log.warning("Field key 'MACEnd' has illegal value")
				log.debug("verify() ending")
				return False

			if 'Confidence' not in self.rec:
				log.warning("Required field key 'Confidence' missing")
				log.debug("verify() ending")
				return False
			elif self.rec['Confidence'] < 1 or self.rec['Confidence'] > 5 or not isinstance(self.rec['Confidence'], int):
				log.warning("Field key 'Confidence' has illegal value")
				log.debug("verify() ending")
				return False

			if 'MediaType' in self.rec:
				if self.rec['MediaType'] == '':
					log.warning("Field key 'MediaType' has illegal value")
					log.debug("verify() ending")
					return False

			if 'DevType' in self.rec:
				if self.rec['DevType'] == '':
					log.warning("Field key 'DevType' has illegal value")
					log.debug("verify() ending")
					return False

			if 'DevModel' in self.rec:
				if self.rec['DevModel'] == '':
					log.warning("Field key 'DevModel' has illegal value")
					log.debug("verify() ending")
					return False

			if 'Note' in self.rec:
				if self.rec['Note'] == '':
					log.warning("Field key 'Note' has illegal value")
					log.debug("verify() ending")
					return False

			if 'WikiLink' in self.rec:
				if self.rec['WikiLink'] == '':
					log.warning("Field key 'WikiLink' has illegal value")
					log.debug("verify() ending")
					return False

			# If we reach here, it's a valid metadata record
			log.debug("verify() ending")
			return True

		else:
			# Shouldn't reach here, so if we do something is corrupt or logic errors
			log.debug("Reached impossible termination point")
			log.debug("verify() ending")
			return False
			
####

	# Function to take a JSON string and populate the object with it. Returns an empty record
	# if the resulting object is not a valid DeepMac record.
	def setJSON(self, j):
		# Create empty records if a blank/null value is passed in
		if j == '' or j == None:
			log.debug("Empty JSON string passed in, creating blank record")
			self.rec = json.loads('{"DeepMac": "registry"}')
		else:
			# Theoretically a valid JSON string, but will fail here if syntax is wrong
			log.debug("setJSON() starting")
			try:
				self.rec = json.loads(j)
			except:
				print "ERROR: Failed to parse JSON string -> " + j
				raise
			
		# Do a verification check, return as result
		result = self.verify()
		log.debug("Verify result = " + str(result))

		log.debug("setJSON() ending")
		return result

####

	# Function to output record in JSON format
	def getJSON(self):
		log.debug("getJSON() starting")

		# Create JSON string based on dictionary
		j = json.dumps(self.rec, ensure_ascii = False, sort_keys=True)
		log.debug("j = " + j)
		
		log.debug("getJSON() ending")
		return j
		
####

	###
	# Functions to get record attributes
	###
	def getType(self):
		if 'DeepMac' in self.rec:
			return self.rec['DeepMac']
		else:
			return False

####

	def getSource(self):
		if 'Source' in self.rec:
			return self.rec['Source']
		else:
			return False

####

	def getEvType(self):
		if 'EventType' in self.rec:
			return self.rec['EventType']
		else:
			return False

####

	def getEvDate(self):
		if 'EventDate' in self.rec:
			return self.rec['EventDate']
		else:
			return False

####

	def getSize(self):
		if 'OUISize' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				return self.rec['OUISize']
			else:
				log.debug("Not a DeepMac registry record")
				return False
		else:
			return False

####

	def getOUI(self):
		if 'OUI' in self.rec:
			if self.rec['DeepMac'] in self.rectypes:
				return self.rec['OUI']
			else:
				log.debug("Not a valid DeepMac record, invalid type %s" % (self.rec['DeepMac']))
				return False
		else:
			return False

####

	def getOrgName(self):
		if 'OrgName' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				return self.rec['OrgName']
			else:
				log.debug("Not a DeepMac registry record")
				return False
		else:
			return False

####

	def getOrgAddr(self):
		if 'OrgAddress' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				if self.rec['OrgName'] == 'PRIVATE':
					return 'PRIVATE'
				else:
					return self.rec['OrgAddress']
			else:
				log.debug("Not a DeepMac registry record")
				return False
		else:
			return False

####

	def getOrgCN(self):
		if 'OrgCountry' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				if self.rec['OrgName'] == 'PRIVATE':
					return 'PRIVATE'
				else:
					return self.rec['OrgCountry']
			else:
				log.debug("Not a DeepMac registry record")
				return False
		else:
			return False

####

	def getMACStart(self):
		if 'MACStart' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				return self.rec['MACStart']
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	def getMACEnd(self):
		if 'MACEnd' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				return self.rec['MACEnd']
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	def getConf(self):
		if 'Confidence' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				return self.rec['Confidence']
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	def getMedia(self):
		if 'MediaType' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'MediaType' in self.rec:
					return self.rec['MediaType']
				else:
					return 'Unknown'
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	def getDevice(self):
		if 'DevType' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'DevType' in self.rec:
					return self.rec['DevType']
				else:
					return 'Unknown'
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	def getModel(self):
		if 'DevModel' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'DevModel' in self.rec:
					return self.rec['DevModel']
				else:
					return 'Unknown'
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	def getNote(self):
		if 'Note' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'Note' in self.rec:
					return self.rec['Note']
				else:
					return 'None'
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

	def getWiki(self):
		if 'WikiLink' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'WikiLink' in self.rec:
					return self.rec['WikiLink']
				else:
					return 'None'
			else:
				log.debug("Not a DeepMac metadata record")
				return False
		else:
			return False

###
# Functions to set record attributes
###
	def setType(self, value):
		if value in self.rectypes:
			self.rec['DeepMac'] = value
			log.debug("Set record type to " + value)
			return True
		else:
			log.debug("Invalid record type '" + value + "' specified")
			return False

####

	def setSource(self, value):
		if value != '':
			self.rec['Source'] = value
			log.debug("Set Source to " + value)
			return True
		else:
			log.debug("Can't have empty Source")
			return False

####

	def setEvType(self, value):
		if value in self.eventtypes:
			self.rec['EventType'] = value
			log.debug("Set event type to " + value)
			return True
		else:
			log.debug("Invalid event type '" + value + "' specified")
			return False

####

	def setEvDate(self, value):
		try:
			datetime.datetime.strptime(value, '%Y-%m-%d')
			self.rec['EventDate'] = value
			log.debug("Set event date to " + value)
			return True
		except ValueError:
			log.debug("Invalid event date '" + value + "' specified")
			return False
			
####

	def setSize(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value in self.ouisizes:
				self.rec['OUISize'] = value
				return True
			else:
				log.debug("Invalid OUI size '" + value +"' specified")
				return False
		else:
			log.debug("Not a DeepMac registry record")
			return False

####

	def setOUI(self, value):
		if self.rec['DeepMac'] == 'registry':
			if 'OUISize' not in self.rec:
				log.warning("OUISize must be set before OUI can be set")
				return False
			elif len(value) <> (self.rec['OUISize'] / 4):
				log.warning("OUI value incorrect length for OUI size")
				return False
			elif not all(char in '0123456789ABCDEF' for char in value):
				log.warning("Invalid OUI '" + value +"' specified")
				return False
			else:
				self.rec['OUI'] = value
				return True
		else:
			log.debug("Not a DeepMac registry record")
			return False

####

	def setOrgName(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value != '':
				self.rec['OrgName'] = value
				return True
			else:
				log.debug("Organization name can't be empty")
				return False
		else:
			log.debug("Not a DeepMac registry record")
			return False

####

	def setOrgAddr(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value != '':
				self.rec['OrgAddress'] = value
				return True
			else:
				log.debug("Organization address can't be empty")
				return False
		else:
			log.debug("Not a DeepMac registry record")
			return False

####

	def setOrgCN(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value != '':
				self.rec['OrgCountry'] = value
				return True
			else:
				log.debug("Organization country can't be empty")
				return False
		else:
			log.debug("Not a DeepMac registry record")
			return False

	def setMACStart(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if len(value) <> 12:
				log.warning("Invalid MAC '" + value + "' specified - Incorrect length")
				return False
			elif not all(char in '0123456789ABCDEF' for char in value):
				log.warning("Invalid MAC '" + value + "' specified - Non-HEX values present")
				return False
			else:
				self.rec['MACStart'] = value
				return True
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	def setMACEnd(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if len(value) <> 12:
				log.warning("Invalid MAC '" + value + "' specified - Incorrect length")
				return False
			elif not all(char in '0123456789ABCDEF' for char in value):
				log.warning("Invalid MAC '" + value + "' specified - Non-HEX values present")
				return False
			else:
				self.rec['MACEnd'] = value
				return True
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	def setConf(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value < 6 and value > 0 and isinstance(value, int):
				self.rec['Confidence'] = value
				return True
			else:
				log.debug("Invalid confidence value '" + value + "' specified")
				return False
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	def setMedia(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['MediaType'] = value
				return True
			else:
				log.debug("Media type can't be empty")
				return False
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	def setDevice(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['DevType'] = value
				return True
			else:
				log.debug("Device type can't be empty")
				return False
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	def setModel(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['DevModel'] = value
				return True
			else:
				log.debug("Device model can't be empty")
				return False
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	def setNote(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['Note'] = value
				return True
			else:
				log.debug("Note can't be empty")
				return False
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	def setWiki(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['WikiLink'] = value
				return True
			else:
				log.debug("Wiki link can't be empty")
				return False
		else:
			log.debug("Not a DeepMac metadata record")
			return False

####

	# Called upon instantiation of object
	def __init__(self, j=u'', rectype='', source='', etype='', edate='', osize='', oui='', orgname=u'', orgadd=u'',
				 orgcn='', mac1='', mac2='', conf='', mtype='', dtype='', dmodel='', note='', wiki=''):
		log.debug("__init__ starting")		 
		self.rec = {}

		# If a JSON string was given, initialize with that first
		if j:
			# TODO: Verify this is a valid JSON string before initializing
			log.debug("j = " + j)
			self.setJSON(j)

		# Run through all keywords that could have been given. We over-write any values already initialized via
		# JSON this way.
		l = locals()
		log.debug("l = " + str(l))
		for var in l.keys():
			log.debug("var = " + var)
			if var in self.fieldmap and l[var] != '':
				log.debug("Matched " + var + " key in fieldmap as " + self.fieldmap[var])
				self.rec[self.fieldmap[var]] = l[var]

				if type(l[var]) != unicode:
					log.debug("Set to value " + str(l[var]))
				else:
					log.debug("Set to value " + l[var].encode('utf8'))
			else:
				log.debug("Not matched in fieldmap")

		log.debug("__init__ ending")
		return None

####

	# Overwriting standard class definitions
	def __eq__(self, other):
		return (self.getEvDate() == other.getEvDate())

	def __lt__(self, other):
		return (self.getEvDate() < other.getEvDate())
