#!/usr/bin/python

# File   : dmRecord.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Class definition for DeepMac records
# Written: 2014/02/04
# Updated: 2019/05/24
### Defines class for a DeepMac record instance, which holds the data for a DeepMac Repository
### record. Includes methods for verifying the data, getting and setting values, etc.

# TODO: Actually raise exceptions with useful information!
# TODO: Finish overriding total_ordering to get comparison / sorting right

# 20180128 - Updated logging levels, replaced printed errors with log statements, similar tweaks.
# 20180129 - Disabled checking of OrgCountry being blank due to frequency of country missing in IEEE data.
#			 Removed use of type() calls, use isinstance() instead.
# 20190521 - Updated method for detecting Private registrations to ignore case.
# 20190522 - Disabled check of blank OrgName in .verify() function, due to inconsistencies in IEEE data format.
# 20190524 - Trivial clean-up of whitespace, commented-out code.

# Required libraries
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

# Pull-in functools decorator for automatic ordering.
#	"Given a class defining one or more rich comparison ordering methods, this class decorator supplies the rest. This simplifies the effort involved in specifying all
#	 of the possible rich comparison # operations:
#	 The class must define one of __lt__(), __le__(), __gt__(), or __ge__(). In addition, the class should supply an __eq__() method."
@functools.total_ordering

###############################################################################

# So it begins
class dmRecord:
	# Initial dictionary for holding record
	rec = {}

	# Internal constants for validating record format
	# TODO: Put these in a constants class to be included in all DeepMac code
	rectypes = ['registry', 'metadata']
	eventtypes = ['add', 'change', 'delete']
	ouisizes = [24, 28, 36]
#	privacyflags = [u'PRIVATE', u'Private']

	# Mapping of class init parameters to DeepMAC record field names, used in initializing an instance
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

	# TODO: Check to make sure all string value tests work regardless if str/unicode type
	def verify(self):
		log.debug("verify() starting")
		status = True

		# Look for DeepMac indicator field
		if 'DeepMac' not in self.rec:
			log.warning("Required field key 'DeepMac' missing")
			status = False
		elif self.rec['DeepMac'] not in self.rectypes:
			log.warning("Field key 'DeepMac' has illegal value")
			status = False

		# Verify common fields for all DeepMac record types
		if 'Source' not in self.rec:
			log.warning("Required field key 'Source' missing")
			status = False
		elif self.rec['Source'] == '':
			log.warning("Field key 'EventType' has illegal value (empty)")
			status = False

		if 'EventType' not in self.rec:
			log.warning("Required field key 'EventType' missing")
			status = False
		elif self.rec['EventType'] not in self.eventtypes:
			log.warning("Field key 'EventType' has illegal value")
			status = False

		if 'EventDate' not in self.rec:
			log.warning("Required field key 'EventDate' missing")
			status = False
		else:
			try:
				datetime.datetime.strptime(self.rec['EventDate'], '%Y-%m-%d')
			except ValueError:
				log.warning("Field key 'EventDate' has illegal value")
				status = False

		# Depending on record type, verify remaining possible fields
		if self.rec['DeepMac'] == 'registry':
			if 'OUISize' not in self.rec:
				log.warning("Required field key 'OUISize' missing")
				status = False
			elif self.rec['OUISize'] not in self.ouisizes:
				log.warning("Field key 'OUISize' has illegal value")
				status = False

			if 'OUI' not in self.rec:
				log.warning("Required field key 'OUI' missing")
				status = False
			if len(self.rec['OUI']) <> (self.rec['OUISize'] / 4):
				log.warning("Field key 'OUI' has illegal value (incorrect length for OUI size)")
				status = False
			elif not all(char in '0123456789ABCDEF' for char in self.rec['OUI']):
				log.warning("Field key 'OUI' has illegal value (non-HEX digits)")
				status = False

			if 'OrgName' not in self.rec:
				log.warning("Required field key 'OrgName' missing")
				status = False
# Disabled check on 2019-05-19. Too many cases of private registrations having a blank OrgName, :(
#			if self.rec['OrgName'] == '' :
#				log.warning("Field key 'OrgName' has illegal value")
#				status = False

			# Only public registry entries should have address info
			if self.rec['OrgName'].lower() != u'private' and self.rec['OrgName'] != '':
				if 'OrgAddress' not in self.rec:
					log.warning("Required field key 'OrgAddress' missing")
					status = False
				if self.rec['OrgAddress'] == '':
					log.warning("Field key 'OrgAddress' has illegal value")
					status = False

				if 'OrgCountry' not in self.rec:
					log.warning("Required field key 'OrgCountry' missing")
					status = False
				# Originally we were going to consider a record bad with no country, but IEEE data now frequently has
				# bad entries with missing addresses, countries, etc. Disabled this check as of 1/29/19.
#				if self.rec['OrgCountry'] == '':
#					log.warning("Field key 'OrgCountry' has illegal value")
#					status = False

			# If we reach here, it's a valid registry record
			log.debug("verify() ending")
			return status
		elif self.rec['DeepMac'] == 'metadata':
			if 'MACStart' not in self.rec:
				log.warning("Required field key 'MACStart' missing")
				status = False
			elif len(self.rec['MACStart']) <> 12:
				log.warning("Field key 'MACStart' has illegal value (incorrect length)")
				status = False
			elif not all(char in '0123456789ABCDEF' for char in self.rec['MACStart']):
				log.warning("Field key 'MACStart' has illegal value (invalid HEX digits)")
				status = False

			if 'MACEnd' not in self.rec:
				log.warning("Required field key 'MACEnd' missing")
				status = False
			elif len(self.rec['MACEnd']) <> 12:
				log.warning("Field key 'MACEnd' has illegal value")
				status = False
			elif not all(char in '0123456789ABCDEF' for char in self.rec['MACEnd']):
				log.warning("Field key 'MACEnd' has illegal value")
				status = False

			if 'Confidence' not in self.rec:
				log.warning("Required field key 'Confidence' missing")
				status = False
			elif self.rec['Confidence'] < 1 or self.rec['Confidence'] > 5 or not isinstance(self.rec['Confidence'], int):
				log.warning("Field key 'Confidence' has illegal value")
				status = False

			if 'MediaType' in self.rec:
				if self.rec['MediaType'] == '':
					log.warning("Field key 'MediaType' has illegal value")
					status = False

			if 'DevType' in self.rec:
				if self.rec['DevType'] == '':
					log.warning("Field key 'DevType' has illegal value")
					status = False

			if 'DevModel' in self.rec:
				if self.rec['DevModel'] == '':
					log.warning("Field key 'DevModel' has illegal value")
					status = False

			if 'Note' in self.rec:
				if self.rec['Note'] == '':
					log.warning("Field key 'Note' has illegal value")
					status = False

			if 'WikiLink' in self.rec:
				if self.rec['WikiLink'] == '':
					log.warning("Field key 'WikiLink' has illegal value")
					status = False

			# If we reach here, it's a valid metadata record
			log.debug("verify() ending")
			return status
		else:
			# Shouldn't reach here, so if we do something is corrupt or logic errors
			log.error("Reached impossible termination point")
			log.debug("verify() ending")
			return False

####

	# Function to take a JSON string and populate the object with it. Returns True if
	# the resulting state of the record is good, otherwise returns False.
	# TODO: Fail if not passed a str/unicode value
	def setJSON(self, j):
		log.debug("setJSON() starting")

		# Create empty records if a blank/null value is passed in
		if j in ['', None]:
			log.info("Empty JSON string passed in, creating blank record")
			self.rec = json.loads('{"DeepMac": "registry"}')
		else:
			# Theoretically a valid JSON string, but will fail here if syntax is wrong
			try:
				self.rec = json.loads(j)
			except Exception as e:
				log.error("Failed to parse JSON string -> %s" % (j.encode('utf8')))
				log.error("Exception triggered: %s" % (e))
				raise

		# Do a verification check, return as result
		result = self.verify()
		log.debug("Verify result = %s" % (str(result)))

		log.debug("setJSON() ending")
		return result

####

	# Function to output record in JSON format (string).
	def getJSON(self):
		log.debug("getJSON() starting")

		# Create JSON string based on dictionary. JSON keys are sorted and non-ASCII characters are left as-is
		j = json.dumps(self.rec, ensure_ascii = False, sort_keys=True)
		log.debug("j = %s" % j.encode('utf8'))

		log.debug("getJSON() ending")
		return j

###
# Functions to get record attributes
###

	# Returns the record type, or False if the type isn't specified
	def getType(self):
		if 'DeepMac' in self.rec:
			return self.rec['DeepMac']
		else:
			return False

####

	# Returns the source for the record, or False if Source not specified
	def getSource(self):
		if 'Source' in self.rec:
			return self.rec['Source']
		else:
			return False

####

	# Returns the Event Type for the record, or False if Event Type not specified
	def getEvType(self):
		if 'EventType' in self.rec:
			return self.rec['EventType']
		else:
			return False

####

	# Returns the Event Date for the record, or False if Event Date not specified
	def getEvDate(self):
		if 'EventDate' in self.rec:
			return self.rec['EventDate']
		else:
			return False

####

	# Returns the OUI size for the record, or False if OUI Size not specified
	def getSize(self):
		if 'OUISize' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				return self.rec['OUISize']
			else:
				log.warn("Not a DeepMac registry record")
				return False
		else:
			return False

####

	# Returns the OUI for the record, or False if OUI not specified
	def getOUI(self):
		if 'OUI' in self.rec:
			if self.rec['DeepMac'] in self.rectypes:
				return self.rec['OUI']
			else:
				log.warn("Not a valid DeepMac record, invalid type %s" % (self.rec['DeepMac']))
				return False
		else:
			return False

####

	# Returns the Organization Name for the record, or False if Organization Name not specified
	def getOrgName(self):
		if 'OrgName' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				return self.rec['OrgName']
			else:
				log.warn("Not a DeepMac registry record")
				return False
		else:
			return False

####

	# Returns the Organization Address for the record, or False if Organization Address not specified
	def getOrgAddr(self):
		if 'OrgAddress' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				if self.rec['OrgName'].lower() == u'private':
					return u'PRIVATE'
				else:
					return self.rec['OrgAddress']
			else:
				log.debug("Not a DeepMac registry record")
				return False
		else:
			return False

####

	# Returns the Organization Country for the record, or False if Organization Country not specified
	def getOrgCN(self):
		if 'OrgCountry' in self.rec:
			if self.rec['DeepMac'] == 'registry':
				if self.rec['OrgName'].lower() == u'private':
					return u'PRIVATE'
				else:
					return self.rec['OrgCountry']
			else:
				log.debug("Not a DeepMac registry record")
				return False
		else:
			return False

####

	# Returns the starting MAC address for the record (metadata types only), or False if not specified
	def getMACStart(self):
		if 'MACStart' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				return self.rec['MACStart']
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	# Returns the ending MAC address for the record (metadata types only), or False if not specified
	def getMACEnd(self):
		if 'MACEnd' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				return self.rec['MACEnd']
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	# Returns the confidence level for the record (metadata types only), or False if not specified
	def getConf(self):
		if 'Confidence' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				return self.rec['Confidence']
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	# Returns the Media Type for the record (metadata types only), or False if not specified
	def getMedia(self):
		if 'MediaType' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'MediaType' in self.rec:
					return self.rec['MediaType']
				else:
					return 'Unknown'
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	# Returns the Device Type for the record (metadata types only), or False if not specified
	def getDevice(self):
		if 'DevType' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'DevType' in self.rec:
					return self.rec['DevType']
				else:
					return 'Unknown'
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	# Returns the Device Model for the record (metadata types only), or False if not specified
	def getModel(self):
		if 'DevModel' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'DevModel' in self.rec:
					return self.rec['DevModel']
				else:
					return 'Unknown'
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

####

	# Returns the Notes for the record (metadata types only), or False if not specified
	def getNote(self):
		if 'Note' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'Note' in self.rec:
					return self.rec['Note']
				else:
					return 'None'
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

	# Returns the Wiki Link for the record (metadata types only), or False if not specified
	def getWiki(self):
		if 'WikiLink' in self.rec:
			if self.rec['DeepMac'] == 'metadata':
				if 'WikiLink' in self.rec:
					return self.rec['WikiLink']
				else:
					return 'None'
			else:
				log.warn("Not a DeepMac metadata record")
				return False
		else:
			return False

###
# Functions to set record attributes
###
	# Sets the type for the record. Returns True if successful or False if invalid value given.
	def setType(self, value):
		if value in self.rectypes:
			self.rec['DeepMac'] = value
			log.debug("Set record type to %s" % (value))
			return True
		else:
			log.warn("Invalid record type '%s' specified" % (value))
			return False

####

	# Sets the Source for the record. Returns True if successful or False if invalid value given.
	def setSource(self, value):
		# TODO: Make Source a more explicit list set of allowed values/types

		if value != '':
			self.rec['Source'] = value
			log.debug("Set Source to %s" % (value))
			return True
		else:
			log.warn("Can't have empty Source")
			return False

####

	# Sets the Event Type for the record. Returns True if successful or False if invalid value given.
	def setEvType(self, value):
		if value in self.eventtypes:
			self.rec['EventType'] = value
			log.debug("Set event type to %s" % (value))
			return True
		else:
			log.warn("Invalid event type '%s' specified" % (value))
			return False

####

	# Sets the Event Date for the record. Returns True if successful or False if invalid value given.
	def setEvDate(self, value):
		try:
			datetime.datetime.strptime(value, '%Y-%m-%d')
			self.rec['EventDate'] = value
			log.debug("Set event date to %s" % (value))
			return True
		except ValueError:
			log.warn("Invalid event date '%s' specified" % (value))
			return False

####

	# Sets the OUI Size for the record. Returns True if successful or False if invalid value given.
	def setSize(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value in self.ouisizes:
				self.rec['OUISize'] = value
				return True
			else:
				log.debug("Invalid OUI size '%s' specified" % (value))
				return False
		else:
			log.warn("Not a DeepMac registry record")
			return False

####

	# Sets the OUI for the record. Returns True if successful or False if invalid value given.
	def setOUI(self, value):
		if self.rec['DeepMac'] == 'registry':
			if 'OUISize' not in self.rec:
				log.warn("OUISize must be set before OUI can be set")
				return False
			elif len(value) <> (self.rec['OUISize'] / 4):
				log.warn("OUI value incorrect length for OUI size")
				return False
			elif not all(char in '0123456789ABCDEF' for char in value):
				log.warn("Invalid OUI '%s' specified" % (value))
				return False
			else:
				self.rec['OUI'] = value
				return True
		else:
			log.warn("Not a DeepMac registry record")
			return False

####

	# Sets the Organization Name for the record. Returns True if successful or False if invalid value given.
	def setOrgName(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value != '':
				self.rec['OrgName'] = value
				return True
			else:
				log.warn("Organization name can't be empty")
				return False
		else:
			log.warn("Not a DeepMac registry record")
			return False

####

	# Sets the Organization Address for the record. Returns True if successful or False if invalid value given.
	def setOrgAddr(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value != '':
				self.rec['OrgAddress'] = value
				return True
			else:
				log.warn("Organization address can't be empty")
				return False
		else:
			log.warn("Not a DeepMac registry record")
			return False

####

	def setOrgCN(self, value):
		if self.rec['DeepMac'] == 'registry':
			if value != '':
				self.rec['OrgCountry'] = value
				return True
			else:
				log.warn("Organization country can't be empty")
				return False
		else:
			log.warn("Not a DeepMac registry record")
			return False

	def setMACStart(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if len(value) <> 12:
				log.warn("Invalid MAC '%s' specified - Incorrect length" % (value))
				return False
			elif not all(char in '0123456789ABCDEF' for char in value):
				log.warn("Invalid MAC '%s' specified - Non-HEX values present" % (value))
				return False
			else:
				self.rec['MACStart'] = value
				return True
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	def setMACEnd(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if len(value) <> 12:
				log.warn("Invalid MAC '%s' specified - Incorrect length" % (value))
				return False
			elif not all(char in '0123456789ABCDEF' for char in value):
				log.warn("Invalid MAC '%s' specified - Non-HEX values present" % (value))
				return False
			else:
				self.rec['MACEnd'] = value
				return True
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	def setConf(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value < 6 and value > 0 and isinstance(value, int):
				self.rec['Confidence'] = value
				return True
			else:
				log.warn("Invalid confidence value '%s' specified" % (value))
				return False
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	def setMedia(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['MediaType'] = value
				return True
			else:
				log.warn("Media type can't be empty")
				return False
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	def setDevice(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['DevType'] = value
				return True
			else:
				log.warn("Device type can't be empty")
				return False
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	def setModel(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['DevModel'] = value
				return True
			else:
				log.warn("Device model can't be empty")
				return False
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	def setNote(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['Note'] = value
				return True
			else:
				log.warn("Note can't be empty")
				return False
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	def setWiki(self, value):
		if self.rec['DeepMac'] == 'metadata':
			if value != '':
				self.rec['WikiLink'] = value
				return True
			else:
				log.warn("Wiki link can't be empty")
				return False
		else:
			log.warn("Not a DeepMac metadata record")
			return False

####

	####
	#### Overwriting standard class definitions
	####
	
	# Called upon instantiation of object
	def __init__(self, j=None, rectype=None, source=None, etype=None, edate=None, osize=None, oui=None, orgname=None,
				 orgadd=None, orgcn=None, mac1=None, mac2=None, conf=None, mtype=None, dtype=None,
				 dmodel=None, note=None, wiki=None):
		log.debug("__init__ starting")		 
		self.rec = {}

		# If first parameter is a string, initialize using it as a JSON string
		if isinstance(j, (str, unicode)):
			# JSON validation will be done in SetJSON, throws exception if invalid
			log.debug("String passed in. Treating as JSON for initialization")
			log.debug("\tj = %s" % (j.encode('utf8')))
			if not self.setJSON(j):
				log.error("Could not initialize dmRecord instance, failed verify check.")
				log.error("\t(JSON valid but DeepMac-specific requirements for record not met, see documentation)\n")
				sys.exit(666)
		# If it's a dict instead, directly pass to the "private" dict (stupid python)
		elif isinstance(j, dict):
			log.debug("Dictionary passed in, using as new record")
			log.debug("j = %s" % (str(j)))
			self.rec = j
		# Ok this isn't a type we support, bugger off
		elif j != None:
			log.debug("Invalid type passed as first parameter: %s" % (str(type(j))))
			log.debug("j = %s" % (str(j)))
			log.error("Invalid type passed as first parameter, must be dict, str or unicode!\n")
			sys.exit(666)
			
		# Run through all keywords that could have been given. We over-write any values already initialized via
		# JSON this way.
		log.debug("Checking for additional passed parameters...")
		l = locals()
		for var in l.keys():
			if var in self.fieldmap:
				log.debug("\tMatched '%s' key in fieldmap as '%s'" % (var, self.fieldmap[var]))
				if l[var] != None:
					ltype = type(l[var])
					log.debug("\t\tType of value is %s" % (str(ltype)))

					# Assign the value to our internal record dictionary
					self.rec[self.fieldmap[var]] = l[var]
					log.debug("\t\tSet to value %s" % (l[var]))
				else:
					log.debug("\t\tNot initialized in call")
			else:
				log.debug("\tLocal variable '%s' not matched in fieldmap" % (str(var)))

		# TODO: Maybe issue warning that the record isn't verified yet? Do a verify but don't except if it's invalid?

		log.debug("__init__ ending")
		return None

	# Functions for comparing two dmRecord instances based solely on event date. Allows for sorting lists of dmRecords
	# NOTE: Will NOT evaluate any other fields and shouldn't be used to compare records for any other purpose.
	def __lt__(self, other):
		return (self.getEvDate() < other.getEvDate())

	def __le__(self, other):
		return (self.getEvDate() <= other.getEvDate())

	def __eq__(self, other):
		return (self.getEvDate() == other.getEvDate())

	def __gt__(self, other):
		return (self.getEvDate() > other.getEvDate())

	def __ge__(self, other):
		return (self.getEvDate() >= other.getEvDate())

####

# End-Of-Line