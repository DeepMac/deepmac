#!/usr/bin/python

# File   : dmManager.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Class definition for DeepMac Repository Manager
# Written: 2014/04/25
# Updated: 2017/08/14

# TODO: Add additional functions:
# TODO: 	Metadata manipulation functions
# TODO: 	Statistics reporting?
# TODO: Update logging to make better use of levels (DEBUG, ERROR, WARNING, etc)

# Library of functions for managing records in DeepMac journals. Supports multiple back-end storage
# methods (coming soon!), searching journals using multiple criteria, and updating journals with new
# DeepMac records.
# The dmManager library is the heart of the DeepMac Project's automation of tracking
# official IEEE hardware address registry changes and associated metadata from multiple sources.

import sys
import os
import re
import logging
import codecs
import simplejson as json
from deepmac_record_class import dmRecord
from deepmac_connector import dmConnector

# Logging configuration
log = logging.getLogger('dm_mgr')
handler = logging.StreamHandler()
logformat = logging.Formatter("%(asctime)s - %(name)s %(levelname)s: %(message)s")
handler.setFormatter(logformat)
log.addHandler(handler)
log.setLevel(logging.ERROR)

					###### Filesystem Interface ######

# Function to check if a specific OUI is private or not, via filesystem connection
def ispriv_by_file(dmmgr, oui):
	log.debug("priv_by_file() starting")
	# dmmgr is an instance of the dmManager class, oui is the OUI value to check
	# This function assumes dmmgr has a valid connection and the OUI given is a valid format!
	path = dmmgr.dmh.mkOUIPath(oui)

	### Check if directory exists, if not then we return None.
	if not os.path.isdir(path):
		log.debug("Path %s does not exist, returning None" % (path))
		log.debug("priv_by_file() ending")
		return None

	# Check if the .private flag file exists.
	if os.path.isfile(path + '.private'):
		log.debug(".private flag file detected, returning True.")
		log.debug("priv_by_file() ending")
		return True

	# No flag file found so return False
	log.debug("No .private flag file detected, returning False.")
	log.debug("priv_by_file() ending")
	return False


# Function to check if a specific OUI is deleted or not, via filesystem connection
def isdel_by_file(dmmgr, oui):
	log.debug("isdel_by_file() starting")
	# dmmgr is an instance of the dmManager class, oui is the OUI value to check
	# This function assumes dmmgr has a valid connection and the OUI given is a valid format!
	path = dmmgr.dmh.mkOUIPath(oui)

	### Check if directory exists, if not then we return None.
	if not os.path.isdir(path):
		log.debug("Path %s does not exist, returning None" % (path))
		log.debug("isdel_by_file() ending")
		return None

	# Check if the .deleted flag file exists.
	if os.path.isfile(path + '.deleted'):
		log.debug(".deleted flag file detected, returning True.")
		log.debug("isdel_by_file() ending")
		return True

	# No flag file found so return False
	log.debug("No .deleted flag file detected, returning False.")
	log.debug("isdel_by_file() ending")
	return False


# Function to set the Deleted flag for a specific OUI, via the filesystem connection
def setdel_by_file(dmmgr, oui, bool):
	log.debug("setdel_by_file() starting")
	# dmmgr is an instance of the dmManager class, oui is the OUI value to set, bool is a true/false flag
	# This function assumes dmmgr has a valid connection and the OUI given is a valid format!
	path = dmmgr.dmh.mkOUIPath(oui)

	### Check if directory exists, if not then we return None.
	if not os.path.isdir(path):
		log.debug("Path %s does not exist, returning None" % (path))
		log.debug("setdel_by_file() ending")
		return None

	# Check if the .deleted flag file exists.
	if os.path.isfile(path + '.deleted'):
		# If the flag is True, nothing to actually do and we're successful
		if bool == True:
			log.debug(".deleted flag already exists")
			log.debug("setdel_by_file() ending")
			return True
		else:
			# Need to delete this flag file
			stat = os.remove(path + '.deleted')
			if stat:
				log.debug(".deleted flag successfully removed")
				log.debug("setdel_by_file() ending")
				return True
			else:
				log.debug(".deleted flag could not be removed!")
				log.debug("setdel_by_file() ending")
				return False			
	else:
		# If the bool flag is False, nothing to do and we're successful
		if bool == False:
			log.debug(".deleted flag doesn't exist, nothing to do")
			log.debug("setdel_by_file() ending")
			return True
		else:
			# Create an empty file to indicate the OUI is deleted from the registry
			try:
				fh = open(path + '.deleted', 'w')
				fh.close()
			except:
				print "FAILURE: Could not create %s file" % (path + '.deleted')
				raise

			stat = os.path.isfile(path + '.deleted')
			if stat:
				log.debug(".deleted flag successfully created")
				log.debug("setdel_by_file() ending")
				return True
			else:
				log.debug(".deleted flag could not be created!")
				log.debug("setdel_by_file() ending")
				return False


# Function to set the Private flag for a specific OUI, via the filesystem connection
def setpriv_by_file(dmmgr, oui, bool):
	log.debug("setpriv_by_file() starting")
	# dmmgr is an instance of the dmManager class, oui is the OUI value to set, bool is a true/false flag
	# This function assumes dmmgr has a valid connection and the OUI given is a valid format!
	path = dmmgr.dmh.mkOUIPath(oui)

	### Check if directory exists, if not then we return None.
	if not os.path.isdir(path):
		log.debug("Path %s does not exist, returning None" % (path))
		log.debug("setpriv_by_file() ending")
		return None

	# Check if the .private flag file exists.
	if os.path.isfile(path + '.private'):
		# If the flag is True, nothing to actually do and we're successful
		if bool == True:
			log.debug(".private flag already exists")
			log.debug("setpriv_by_file() ending")
			return True
		else:
			# Need to delete this flag file
			stat = os.remove(path + '.private')
			if stat:
				log.debug(".private flag successfully removed")
				log.debug("setpriv_by_file() ending")
				return True
			else:
				log.debug(".private flag could not be removed!")
				log.debug("setpriv_by_file() ending")
				return False			
	else:
		# If the bool flag is False, nothing to do and we're successful
		if bool == False:
			log.debug(".private flag doesn't exist, nothing to do")
			log.debug("setpriv_by_file() ending")
			return True
		else:
			# Create an empty file to indicate the OUI is deleted from the registry
			try:
				fh = open(path + '.private', 'w')
				fh.close()
			except:
				print "FAILURE: Could not create %s file" % (path + '.private')
				raise

			stat = os.path.isfile(path + '.private')
			if stat:
				log.debug(".private flag successfully created")
				log.debug("setpriv_by_file() ending")
				return True
			else:
				log.debug(".private flag could not be created!")
				log.debug("setpriv_by_file() ending")
				return False


# Function to get all records for an OUI via filesystem connection
def get_by_file(dmmgr, oui):
	log.debug("get_by_file() starting")
	# dmmgr is an instance of the dmManager class, oui is the OUI value to get
	# This function assumes dmmgr has a valid connection and the OUI given is a valid format!
	results = []
	path = dmmgr.dmh.mkOUIPath(oui)

	### Check if directory exists, if not there's no records so return an empty set
	if not os.path.isdir(path):
		log.debug("Path %s does not exist, returning empty set" % (path))
		return results

	# Make the file file specification and store in its own variable
	fname = path + "records"

	# Check if there's record file in directory, if not there's no records so return empty set
	if not os.path.isfile(fname):
		# TODO: Fix so access errors are reported explicitly, versus file just not existing
		log.debug("No record file found in %s or inaccessible, returning empty set" % (path))
		return results

	# Open the record file, bail if error occurs
	try:
		fh = codecs.open(fname, 'r', encoding='utf-8')
	except:
		print "ERROR: Couldn't open file %s for reading." % (fname)
		raise

	# Read record file contents
	try:
		jarr = json.load(fh)
	except:
		print "ERROR: Unknown error while trying to read file %s" % (fname)
		raise

	# Close the record file
	fh.close()

	# Process JSON array to an array of DeepMac record objects
	for r in jarr['recs']:
			rec = dmRecord(j = r)
			if rec.rec == {}:
					print "WARNING: Record could not be created for JSON string %s" % (line)

			# Append to our results set
			results.append(rec)

	# Return the results set
	log.debug("get_by_file() ending")
	return results


# Function to append a dmRecord instance to the repository via a dmManager instance.
def add_by_file(dmmgr, rec):
	# dmmgr is an instance of the dmManager class, rec is a dmRecord instance to append.
	# This function assumes dmmgr has a valid connection and rec is valid!
	log.debug("add_by_file() starting")
	result = False
	
	# TODO: Handle conditions related to registry entry deleted or going private:
		# 1. Existing entry is deleted (DeepMac = 'registry' and Action = 'del').
		# 2. Deleted entry is re-registered (.deleted exists, DeepMac = 'registry' and Action = 'add').
		# 3. Existing public entry is marked private (DeepMac = 'registry' and Action = 'change' and OrgName = 'PRIVATE').
		# 4. Existing private entry goes Public (.private exists, DeepMac = 'registry' and Action = 'change' and OrgName != 'PRIVATE').

	# Get the OUI from this record.
	oui = rec.getOUI()

	# Get a path for this OUI.
	path = dmmgr.dmh.mkOUIPath(oui)

	# Check if directory exists. If not, attempt to make it
	if not os.path.exists(path):
		log.debug("Path %s does not exist, attempting to create." % (path))
		try:
			os.makedirs(path, 0750)
		except OSError as err:
			print "ERROR: Couldn't make directory %s, aborting." % (path)
			print "(Actual error message was: %s)" % (path)
			raise
		log.debug("Path %s successfully created." % (path))

	# Make the fully qualified filename.
	fname = path + "records"

	# Check if journal already exists
	if os.path.isfile(fname):
		# If it does, read it in and close the file. Fail if any errors occur
		log.debug("Attempting to load journal file")
		try:
			fh = codecs.open(fname, 'r', encoding='utf-8')
			jarr = json.load(fh)
		except:
			print "ERROR: Unknown error while trying to update file %s (read-in)" % (fname)
			raise

		# Close the file
		fh.close()
	else:
		# File doesn't exist, create an empty JSON array to use
		log.debug("Journal file doesn't exist, stubbing dict")
		jarr = {'recs': []}
		
	# Append our new record to the JSON array
	jarr['recs'].append(rec.rec)
	log.debug("Added new record to JSON array")

	# Open file for writing and attempt to write new JSON array
	log.debug("Attempting to write updated journal")
	try:
		fh = codecs.open(fname, 'w', encoding='utf-8')
		json.dump(jarr, fh, ensure_ascii = False, indent = "\t", sort_keys = True)
	except:
		print "ERROR: Unknown error while trying to update file %s (write-out)" % (fname)
		raise
	log.debug("Successfully updated journal file.")

	# Close file
	fh.close()

	# Since (presumably) no errors occurred, set result to True
	result = True

	# Return the result status
	log.debug("add_by_file() ending")
	return result



# Function to enumerate OUIs in the repository and return as a list
def enum_by_file(dmmgr, sz, prvflag, delflag):
	# dmmgr is an instance of the dmManager class. This function assumes dmmgr has a valid connection!
	# sz is the OUI size(s) to be checked, prvflag is for private records, delflag is for deleted records
	# NOTE: If not specified in original call, prvflag will be True and delflag will be False
	log.debug("enum_by_file() starting")
	log.debug("dmmgr.dmh.addr = %s" % (dmmgr.dmh.addr))
	log.debug("sz = %s" % (sz))
	log.debug("prvflag = %s" % (prvflag))
	log.debug("delflag = %s" % (delflag))
	results = []

	# Walk through the repository directory tree
	for entry in os.walk(dmmgr.dmh.addr):
#		log.debug("entry = %s" % (str(entry)))
		# Check if this entry is for a records file
		if 'records' in entry[2]:
			# Break off root path and remove slashes
			dir = re.sub(dmmgr.dmh.addr, '', entry[0])
			dir = re.sub('/', '', dir)
			log.debug("dir = %s" % (dir))
			
			# Check if this OUI is a size we care about
			if sz == 0 or len(dir) == sz/4:
				# Check flags 
				if prvflag == False and dmmgr.isPrivate(dir):
					# Skip this entry
					continue

				if delflag == False and dmmgr.isDeleted(dir):
					# Skip this entry
					continue

				# Entry matches all conditions, add this OUI to our results
				results.append(dir)
				log.debug("Appended %s to results" % (dir))

	### Return the result status
	log.debug("enum_by_file() ending")
	return results

					###### Primary Manager Class ######

class dmManager:
	# Function to verify a string is in a valid OUI format.
	# Returns True if it is valid, otherwise will return False.
	def chkoui(self, oui):
		log.debug("chkoui() starting")
		log.debug("oui = %s" % (oui))

		# Colons and hyphens are typically used as separators so they are ignored.
		oui = re.sub('[:\-]', '', oui)
		
		# A valid OUI specification is only hex digits, and will be 6, 7, or 9 characters long.
		if len(oui) not in (6, 7, 9):
			log.debug("OUI is an unexpected length of %d" % (len(oui)))
			return False

		# Try and convert to an integer. This will fail if it's not a valid hexadecimal number
		try:
			int(oui, 16)
		except:
			log.debug("OUI contains non-HEX characters (other than valid separators)")
			return False

		log.debug("OUI value is valid")
		log.debug("chkoui() ending")
		return True


	# Method for getting all records for a specific OUI. Returns a list of dmRecord types,
	# or an empty list if there are no records. Returns None if there is an error.
	# TODO: Update the .get() function to allow optional filtering by record type, other fields
	def get(self, oui):
		# 'oui' is the OUI to get records for. This can be a MA-L, MA-M or MA-S number.
		log.debug("get() starting")
		log.debug("oui = %s" % (oui))

		# Check if the OUI specified is in a valid format, bail if not
		if not self.chkoui(oui):
			print "WARNING: An invalid OUI of %s was specified for the get operation." % (oui)
			return None

		# Verify we have an active connection to the repository
		if not self.dmh.isConnected():
			print "ERROR: A connection to the repository is not established. Can't read."
			return None

		# Use connection type to determine how to pull records. Call the appropriate external
		# function and pass in a copy of the dmManager instance along with the oui given.
		if self.dmh.type == 'filesystem':
			results = get_by_file(self, oui)
		elif self.dmh.type == 'web':
			results = get_by_web(self, oui)
		elif self.dmh.type == 'database':
			results = get_by_db(self, oui)
		else:
			print "ERROR: Unrecognized repository connection type, can't continue!"
			sys.exit(666)

		# Sort the results. Default sorting is by the event dates
		# TODO: Verify this will actually sort correctly!
		# TODO: Move sorting into the get_by_* functions instead of here
		results.sort()

		log.debug("get() ending")
		return results


	# Method for appending a record to the repository (i.e. journaling). Takes a
	# dmRecord object as input. The record, if valid, is used to determine where to
	# store the data and then the appropriate entry is appended to the record.
	# Returns True if the operation was successful, otherwise returns False.
	def append(self, record):
		log.debug("append() starting")
		log.debug("record = %s" % (str(record)))

		# Verify we have an active connection to the repository
		if not self.dmh.isConnected():
			print "ERROR: A connection to the repository is not established. Can't append."
			return False

		# Verify this record is in a valid state before allowing it to be recorded
		if not record.verify():
			print "ERROR: Record is not in a valid state. Can not append!"
			result = False
		else:
			# Use connection type to determine how to append record. Call the appropriate external
			# function and pass in a copy of the dmManager instance along with the record given.
			if self.dmh.type == 'filesystem':
				result = add_by_file(self, record)
			elif self.dmh.type == 'web':
				result = add_by_web(self, record)
			elif self.dmh.type == 'database':
				result = add_by_db(self, record)
			else:
				print "ERROR: Unrecognized repository connection type, can't continue!"
				raise

		log.debug("append() ending")
		return result


	# Method for enumerating entries in the repository. Returns a list of OUIs currently
	# in the repository. Optional flags control what size OUIs are looked at and if entries
	# flagged private/deleted are included.
	# sz	  - Size of OUIs to enumerate. Default value of 0 means all. Otherwise, the value
	# 		    is treated as the bitsize of the OUI (i.e. 24, 36, etc)
	# prvflag - Boolean flag indicating if PRIVATE OUIs are to be included (default is True, include them)
	# delflag - Boolean flag indicating if deleted OUI entries are to be included (default is False, do not include them)
	def enumerate(self, sz = 0, prvflag = True, delflag = False):
		log.debug("enumerate() starting")
		results = None
		
		# Validate sz parameter
		if sz > 0 and sz not in (dmRecord.ouisizes):
			print "ERROR: sz is not a valid OUI size (%d)" % (sz)
			return results

		# Determine which enumeration process to use based on connection type
		if self.dmh.type == 'filesystem':
			results = enum_by_file(self, sz, prvflag, delflag)
		elif self.dmh.type == 'web':
			results = enum_by_web(self, sz, prvflag, delflag)
		elif self.dmh.type == 'database':
			results = enum_by_db(self, sz, prvflag, delflag)
		else:
			print "ERROR: Unrecognized repository connection type, can't continue!"
			sys.exit(666)

		log.debug("%d total results." % (len(results)))
		log.debug("enumerate() ending")
		return results


	# Method for searching repository for all records matching specific criteria
	def search(self, oui, date, orgname, orgaddress):
		log.debug("search() starting")
		# Log the params given

		# Verify at least one search parameter given, return error if not
		# Check each parameter to verify it's searchable for the given field
		# Perform any case conversions

		# TODO: Write actual search code! :/

		log.debug("search() ending")
		return None


	# Function to determine if a specific OUI entry is marked as Private or not.
	# Returns True if private, False if public. A value of None is returned if
	# there is an error/problem, or the OUI doesn't exist in the repository.
	def isPrivate(self, oui):
		log.debug("isPrivate() starting")

		# Check if the OUI specified is in a valid format, bail if not
		if not self.chkoui(oui):
			print "WARNING: An invalid OUI of %s was specified for the isPrivate() check." % (oui)
			log.debug("isPrivate() ending")
			return None

		# Verify we have an active connection to the repository
		if not self.dmh.isConnected():
			print "ERROR: A connection to the repository is not established. Can't check private flag."
			log.debug("isPrivate() ending")
			return None

		# Use connection type to determine how to check private status. Call the appropriate external
		# function and pass in a copy of the dmManager instance along with the oui given.
		if self.dmh.type == 'filesystem':
			result = ispriv_by_file(self, oui)
		elif self.dmh.type == 'web':
			result = ispriv_by_web(self, oui)
		elif self.dmh.type == 'database':
			result = ispriv_by_db(self, oui)
		else:
			print "ERROR: Unrecognized repository connection type, can't continue!"
			sys.exit(666)

		# All done, return result of check
		log.debug("isPrivate() ending")
		return result


	# Function to determine if a specific OUI entry is marked as Deleted or not.
	# Returns True if deleted, False if not deleted. A value of None is returned if
	# there is an error/problem, or the OUI doesn't exist in the repository.
	def isDeleted(self, oui):
		log.debug("isDeleted() starting")

		# Check if the OUI specified is in a valid format, bail if not
		if not self.chkoui(oui):
			print "WARNING: An invalid OUI of %s was specified for the isDeleted() check." % (oui)
			log.debug("isDeleted() ending")
			return None

		# Verify we have an active connection to the repository
		if not self.dmh.isConnected():
			print "ERROR: A connection to the repository is not established. Can't check deleted flag."
			log.debug("isDeleted() ending")
			return None

		# Use connection type to determine how to check deleted status. Call the appropriate external
		# function and pass in a copy of the dmManager instance along with the oui given.
		if self.dmh.type == 'filesystem':
			result = isdel_by_file(self, oui)
		elif self.dmh.type == 'web':
			result = isdel_by_web(self, oui)
		elif self.dmh.type == 'database':
			result = isdel_by_db(self, oui)
		else:
			print "ERROR: Unrecognized repository connection type, can't continue!"
			sys.exit(666)

		# All done, return result of check
		log.debug("isDeleted() ending")
		return result


	# Function to set the Deleted flag for a specific OUI in the Repository.
	# Returns True if successful in setting the flag, otherwise returns False.
	# A value of None is returned if
	# there is an error/problem, or the OUI doesn't exist in the repository.
	def setDeleted(self, oui, bool):
		log.debug("setDeleted() starting")
		result = False

		# Check if the OUI specified is in a valid format, bail if not
		if not self.chkoui(oui):
			print "WARNING: An invalid OUI of %s was specified for the setDeleted() function." % (oui)
			log.debug("setDeleted() ending")
			return None

		# Make sure bool is a True or False, anything else is not allowed
		if bool != True and bool != False:
			print "ERROR: Invalid value given for Deleted flag. Must use True or False."
			log.debug("setDeleted() ending")
			return None

		# Verify we have an active connection to the repository
		if not self.dmh.isConnected():
			print "ERROR: A connection to the repository is not established. Can't set deleted flag."
			log.debug("setDeleted() ending")
			return None

		# Use connection type to determine how to check deleted status. Call the appropriate external
		# function and pass in a copy of the dmManager instance along with the oui given.
		if self.dmh.type == 'filesystem':
			result = setdel_by_file(self, oui, bool)
		elif self.dmh.type == 'web':
			result = setdel_by_web(self, oui, bool)
		elif self.dmh.type == 'database':
			result = setdel_by_db(self, oui, bool)
		else:
			print "ERROR: Unrecognized repository connection type, can't continue!"
			sys.exit(666)

		# All done, return result of check
		log.debug("setDeleted() ending")
		return result


	# Function to set the Private flag for a specific OUI in the Repository.
	# Returns True if successful in setting the flag, otherwise returns False.
	# A value of None is returned if there is an error/problem, or the OUI doesn't exist in the repository.
	def setPrivate(self, oui, bool):
		log.debug("setPrivate() starting")
		result = False

		# Check if the OUI specified is in a valid format, bail if not
		if not self.chkoui(oui):
			print "WARNING: An invalid OUI of %s was specified for the setPrivate() function." % (oui)
			log.debug("setPrivate() ending")
			return None

		# Make sure bool is a True or False, anything else is not allowed
		if bool != True and bool != False:
			print "ERROR: Invalid value given for Private flag. Must use True or False."
			log.debug("setPrivate() ending")
			return None

		# Verify we have an active connection to the repository
		if not self.dmh.isConnected():
			print "ERROR: A connection to the repository is not established. Can't set private flag."
			log.debug("setPrivate() ending")
			return None

		# Use connection type to determine how to check deleted status. Call the appropriate external
		# function and pass in a copy of the dmManager instance along with the oui given.
		if self.dmh.type == 'filesystem':
			result = setpriv_by_file(self, oui, bool)
		elif self.dmh.type == 'web':
			result = setpriv_by_web(self, oui, bool)
		elif self.dmh.type == 'database':
			result = setpriv_by_db(self, oui, bool)
		else:
			print "ERROR: Unrecognized repository connection type, can't continue!"
			sys.exit(666)

		# All done, return result of check
		log.debug("setPrivate() ending")
		return result


	# Function to close repository connection, end any processing
	def end(self):
		log.debug("end() starting")

		# Check if there's a valid connection handle, if so disconnect
		if self.dmh.isConnected():
			self.dmh.disconnect()

		log.debug("end() ending")
		return None


	# Called upon instantiation of the object.
	#	'type' is the connection type: filesystem, database, web
	#	'address' is the address for the connection type:
	#	'creds' is optional, and is a list 
	def __init__(self, type, address, creds):
		log.debug("__init__() starting")

		# Create an instance of the connector class here, using the above params.
		self.dmh = dmConnector(type, address, creds)

		# TODO: Check if there was a connection error.

		# Attempt to connect and report error message if there's a failure
		if not self.dmh.connect():
			print "ERROR: Couldn't establish DeepMac repository connection."
			# TODO: Status codes/error messages stored in dmConnector class, access here

			sys.exit(666)
#		else:
#			print "Connection to DeepMac repository established."
		
		log.debug("__init__() ending")
		return None

####

# End-of-line