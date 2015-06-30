#!/usr/bin/python

# File   : dmConnector.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Class definition for DeepMac Repository Connector
# Written: 2014/04/25
# Updated: 2014/12/16

# Used to establish a connection to a DeepMac record repository (aka journal).
# This is an intermediary class, used by the dmManager class in order to communicate with
# the repository. dmConnector will validate connection info, indicate if a connection
# is successful or not and perform other duties related directly to managing the connection.

import os
import logging
from deepmac_record_class import dmRecord

# Logging configuration
log = logging.getLogger('dm_con')
handler = logging.StreamHandler()
logformat = logging.Formatter("%(asctime)s - %(name)s %(levelname)s: %(message)s")
handler.setFormatter(logformat)
log.addHandler(handler)
log.setLevel(logging.ERROR)

####

class dmConnector:
	# Class-wide initializations:
	# Create data values to hold class attributes such as connection type, address, etc.
	type = ''
	addr = ''
	creds = { 'u': None, 'p': None }
	con = None
	
	# Given an OUI (presumed valid), return a full path for the OUI's directory in the repository
	# Note: Does not validate OUI. Does not test if directory exists or not.
	def mkOUIPath(self, oui):
		# If this is not a filesystem connection, return false.
		if self.type != "filesystem":
			return False

		# Convert to standard string. Strip colons and hyphens. Convert to all uppercase.
		oui = str(oui)
		oui = oui.translate(None, ":-").upper()

		# The first 6 characters divided up into three directories in path format.
		hexpath = oui[0:2] + "/" + oui[2:4] + "/" + oui[4:6] + "/"

		# If there's anything past the first 6 characters, add it as its own directory
		if len(oui) > 6:
			hexpath = hexpath + oui[6:] + "/"

		log.debug("hexpath = %s" % (hexpath))

		# Return final path. Address for this connection is the repo base directory.
		return self.addr + hexpath

	# Called upon instantiation of object
	def __init__(self, t, a, c=None):
		log.debug("__init__() starting")
		log.debug("t = %s" % (t))
		log.debug("a = %s" % (a))
		log.debug("c = %s" % (c))
		# 't' is the connection type: filesystem, database, web
		# 'a' is the address for the connection type
		# 'c' is the credentials to connect with and is a list. Ignored for filesystem type

		### Perform some verification checks on params: Make sure type is valid, address isn't empty, etc.
		# Make sure a valid connection type was given
		# TODO: Connection types a global dict or something
		if t not in ('filesystem', 'database', 'web'):
			# TODO: Handle this properly with try/except
			log.debug("ERROR: Invalid connection type specified.")
			exit(1)
		else:
			self.type = t

		### Verify address format based on connection type
		if self.type == 'filesystem':
			# Convert to absolute path format
			# NOTE: Python's handling of standard *nix path expansion is severely broken and not trustworthy.
			# This may arbitrarily break perfectly valid paths for no good reason. Also, even an explicitly
			# given trailing slash is removed.
			self.addr = os.path.abspath(os.path.expanduser(a)) + "/"
		elif self.type == 'web':
			# TODO: Regex to verify address is a valid URL
			self.addr = a
		elif self.type == 'database':
			# TODO: Regex to verify a valid DSN was given
			self.addr = a

		log.debug("self.addr is now %s" % (self.addr))

		### Verify credentials
		# Only need to check creds for DB and web types
		if self.type in ('database', 'web'):
			if c == None:
				log.debug("ERROR: Credentials required for connection type %s" % (self.type))
				exit(1)
			if type(c) is not dict:
				log.debug("ERROR: Credentials must be specified in dict format, not %s" % (type(c)))
				exit(1)
			elif 'u' not in c:
				log.debug("ERROR: Credentials in a dict but missing 'u' key")
				exit(1)
			elif 'p' not in c:
				log.debug("ERROR: Credentials in a dict but missing 'p' key")
				exit(1)
			elif c['u'] == "" or c['u'] == None:
				log.debug("ERROR: Username is missing or blank for credentials")
				exit(1)
			elif c['p'] == "" or c['p'] == None:
				log.debug("ERROR: Password is missing or blank for credentials")
				exit(1)
			else:
				self.creds = c

		log.debug("__init__() ending")
		return None

####

	# Function for connecting to repository. Returns True on a successful connection,
	# otherwise returns False. Connection handle is stored inside class.
	def connect(self):
		log.debug("connect() starting")

		### Attempt to open connection to repository
		# For filesystem types we just make sure the directory exists
		if self.type == 'filesystem':
			# Make sure it exists to start with
			if os.path.exists(self.addr):
				log.debug("Verified path exists")
				# Make sure we have a path and not a file.
				if not os.path.isdir(self.addr):
					log.debug("%s is a file, specify JUST a pathname!" % (self.addr))
					log.debug("connect() ending")
					return False
				else:
					log.debug("Verified path is a directory")
			else:
				log.debug("%s doesn't exist or is inaccessible." % (self.addr))
				log.debug("connect() ending")
				return False
					
			### For success, store the resulting handle in this instance
			# For filesystem connection types there's no access handle to store, so we dupe the pathname
			self.con = self.addr
		elif self.type == 'database':
			### Attempt to open DB connection using address and creds
			### Report any errors and exit/fail if connection unsuccessful
			### For success, store the resulting handle in this instance
			self.con = result
		elif self.type == 'web':
			### Attempt to connect to website using address and creds
			### Report any errors and exit/fail if connection unsuccessful
			### For success, store the resulting handle in this instance
			self.con = result
		else:
			# Should be impossible for this to happen
			print "ERROR: Unrecognised connection type %s" % (self.type)
			log.debug("connect() ending")
			return False

		log.debug("connect() ending")
		return True

####

	# Function for disconnecting from repository
	def disconnect(self):
		log.debug("disconnect() starting")
		if self.type == 'filesystem':
			# For filesystem types, nothing to disconnect

			# Erase connection handle
			self.con = None
			return True
		elif self.type == 'databae':
			### Invoke DB connection method to flush any remaining operation
			### Check DB connection for any error messages, report if found.
			### Invoke DB connection method to logout of database
			### Check DB connection for any error messages, report if found.

			# Erase connection handle
			self.con = None
			return True
		elif self.type == 'web':
			### Invoke web connection method to flush any remaining operation
			### Check web connection for any error messages, report if found.
			### Invoke web connection method to logout of database
			### Check web connection for any error messages, report if found.

			# Erase connection handle
			self.con = None
			return True
		else:
			# Should be impossible for this to happen
			print "ERROR: Unrecognised connection type %s" % (self.type)
			return False

		log.debug("disconnect() starting")
		return True

####
		
	# Function to check if a connection is established or not. Returns True if
	# a valid connection handle is present, otherwise returns False
	def isConnected(self):
		log.debug("isConnected() starting")

		# Check if a connection handle exists or not
		if self.con == None:
			status = False
		else:
			status = True

		log.debug("isConnected() ending")
		return status
