#!/usr/bin/python

# File	 : dmImport.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Import records from the IEEE registry archive into repository
# Written: 2014/06/11
# Updated: 2019/05/28

# 20180124 - Fixed bug with incorrect detection of Private registries (IEEE data format change).
#		     Now checks for uppercase and capitalized versions.
#		   - Fixed bug with incorrectly pulling first record in journal instead of last record.
# 20180129 - Bug fixes to logic for journaling (incorrect comparisons, attempting to append invalid records, etc)
# 20180125 - Adjusted logging levels, added a few more logging statements, a few other tweaks.
# 20190518 - Revised checks for Private registration to ignore case of OrgName field in comparisons.
# 20190522 - Added check for a Private registration's OrgName changing to blank, and updated detection of change
#			 in a registry entry to ignore case. These changes avoid documenting insignificant changes in IEEE registry.
# 20190524 - Revised comparison check between registry records to use a function, and added said function to perform check
#			 without triggering potential exceptions due to inconsistent data format in IEEE registry files.
# 20190528 - Fixed bugs with new compare() function. Hunted down and exterminated final bugs in importation process! :D


import sys
import os
import re
import logging
import datetime
import ConfigParser
from deepmac_manager import dmManager
from deepmac_record_class import dmRecord

# Logging configuration
log = logging.getLogger('dm_import')
handler = logging.StreamHandler()
logformat = logging.Formatter("%(asctime)s - %(name)s %(levelname)s: %(message)s")
handler.setFormatter(logformat)
log.addHandler(handler)
log.setLevel(logging.ERROR)

# Initialization
dupeoui = ('0001C8', '080030')
basedir = '/home/USERDIR/site/reboot/'
cfg = ConfigParser.SafeConfigParser()
cfg.read(basedir + 'dmimport.cfg')

# Attempt to read configuration options
try:
	base = cfg.get('dmimport', 'basedir')
	last = cfg.get('dmimport', 'lastdate')
except ConfigParser.NoSectionError:
	# TODO: If file doesn't exist, create it?
	log.error("No dmimport configuration section found.")
	sys.exit(1)
except ConfigParser.NoOptionError:
	# TODO: If last isn't in file, create last with earliest available date in calendar (?)
	log.error("One or more required options missing from dmimport config file.")
	sys.exit(1)
	
# Normalize our datetime objects
last = datetime.datetime.strptime(last, '%Y-%m-%d').date()
today = datetime.date.today()

# Establish a connection to the DeepMac repository
dm = dmManager('filesystem', basedir + 'journal', '')

log.debug("base = %s" % (base))
log.debug("last = %s" % (last))
log.debug("today = %s" % (today))

# Function to compare to DeepMac records and see if they differ. Uses special rules for importation process
# Could probably be written better, may get re-formulated in move to Python3 in the future.
def compare(rec1, rec2):
	log.debug("compare() function starting")

	# Initialize
	result = False
	name1 = rec1.getOrgName()
	addr1 = rec1.getOrgAddr()
	cntry1 = rec1.getOrgCN()
	name2 = rec2.getOrgName()
	addr2 = rec2.getOrgAddr()
	cntry2 = rec2.getOrgCN()

	# Convert any boolean values to strings. This is a terrible kludge and I shouldn't do it this way.
	# Blanket string conversions on values will throw exceptions in cases where the unicode string contains undecodable characters. All of this will be avoided when moving to Python3.
	log.debug("Checking for any boolean values and converting to strings if found")
	if isinstance(name1, bool): name1 = str(name1)
	if isinstance(addr1, bool): addr1 = str(addr1)
	if isinstance(cntry1, bool): cntry1 = str(cntry1)
	if isinstance(name2, bool): name2 = str(name2)
	if isinstance(addr2, bool): addr2 = str(addr2)
	if isinstance(cntry2, bool): cntry2 = str(cntry2)

	# Perform check
	if name1.lower() == name2.lower() and addr1.lower() == addr2.lower() and cntry1.lower() == cntry2.lower():
		log.debug("Compare gave true result.")
		result = True
	else:
		log.debug("Compare gave false result.")
		result = False

	# Done, return result
	log.debug("compare() function ending")
	return result


#### Main Execution ###

# Loop through dates from last run to current date.
while last <= today:
	# Check if directory exists for this date
	cwd = base + last.strftime('/%Y/%m/%d')
	log.debug("cwd = %s" % (cwd))

	if os.path.isdir(cwd):
		# Cycle through possible OUI files here
		for fname in ('oui.csv', 'oui28.csv', 'oui36.csv', 'iab.csv'):
			log.debug("fname = %s" % (fname))

			# Check if this file exists
			if os.path.isfile(cwd + '/' + fname):
				# Open this file for processing
				try:
					fh = open(cwd + '/' + fname, 'r')
				except Exception as e:
					# TODO: Better error reporting/handling
					log.error("Encountered exception %s trying to open file." % e)
					raise

				# Determine OUI size being processed
				if fname == 'oui.csv':
					osz = 24
				elif fname == 'oui28.csv':
					osz = 28
				elif fname == 'oui36.csv' or fname == 'iab.csv':
					osz = 36
				else:
					log.error("Encountered unexpected import filename. This shouldn't happen.")
					print "ERROR: Encountered unexpected import file. This shouldn't happen."
					sys.exit()
				log.debug("osz = %d" % (osz))

				# Read CSV file and process for new/change/delete actions.
				log.info("Processing %s/%s" % (cwd, fname))
				ouilist = []
				for linenum, line in enumerate(fh):
					if line == "": continue
					log.info("Processing line number %d" % (linenum))

					# TODO: Sanity-check line, make sure tab-delimited and the right number of fields, etc
					fields = line.decode('utf8').rstrip('\n').split('	')
					log.debug('line = %s' % (line))
					log.debug('fields count = %d' % (len(fields)))

					# Extract and normalize OUI string, save in list for later deletion detection
					oui = re.sub('-', '', fields[0])
					if osz > 24: oui = oui + fields[1][0:(osz - 24) / 4]
					ouilist.append(oui)
					log.debug("oui = %s" % (oui))

					# Check organization name to determine if it's a private registration
					oname = fields[2]
					if oname.lower() == u'private' or len(fields) == 3:
						# Private registrations have no address or country of origin. Create a minimal record
						drec = dmRecord(rectype = u'registry', source = u'IEEE', edate = last.strftime('%Y-%m-%d').decode('utf8'), osize = osz, oui = oui, orgname = oname)
						isprv = True
					else:
						log.debug("orgname = %s" % (fields[2]).encode('utf8'))

						# Not a private registration - Extract country
						ispriv = False
						if len(fields) < 8:
							country = u'Unspecified'
						else:
							country = fields[8]
						log.debug("country = %s" % (country))

						# Extract and normalize address
						oa = '\\n'.join(fields[3:7]).strip()
						if not oa:
							oa = u'Not listed in registry'
						log.debug("oa = %s" % (oa.encode('utf8')))

						# Create a full record for this OUI registry entry
						drec = dmRecord(rectype = u'registry', source = u'IEEE', edate = last.strftime('%Y-%m-%d').decode('utf8'), osize = osz, oui = oui, orgname = oname, orgadd = oa, orgcn = country)

					# Check if any existing records exist for this OUI
					delflag = None	#\_
					prvflag = None	#/  Use None to indicate no flag change, T/F to indicate flag change and to what state
					recs = dm.get(oui)
					if recs:
						log.info("Existing records for OUI %s found" % (oui))

						# Copy most recent entry for this OUI from journal.
						orec = recs[-1]

						# Check if any changes between most recent record in journal and our current record in hand
						if not compare(drec, orec):
							# Absurdly we must "whitelist" several OUIs as they are duplicated in the official registry files, :(
							if orec.getOUI() in dupeoui:
								log.info("Skipping whitelisted OUI %s" % (oui))
								continue

							# Handle cases were OrgName is blank and record may be a private registration.
							if orec.getOrgName().lower() == u'private' and drec.getOrgName() == '':
								continue

							# Records differ - if previous record isn't a delete action then append this as a change record
							if orec.getEvType() != 'delete':
								log.info("Previous entry for OUI %s wasn't a delete action, so this is a change." % (oui))
								drec.setEvType('change')

								# Check if this OUI changed to/from private, set flag accordingly.
								if drec.getOrgName().lower() == u'private' and orec.getOrgName().lower() != u'private':
									log.info("OUI %s switched to private registry." % (oui))
									prvflag = True
								elif drec.getOrgName().lower() != u'private' and orec.getOrgName().lower() == u'private':
									log.info("OUI %s switched to public registry." % (oui))
									prvflag = False
							else:
								# Last record was deletion of data, record this as a new add and turn off the deleted flag
								log.info("Previously deleted OUI %s has been re-registered, so this is an add." % (oui))
								drec.setEvType('add')
								delflag = False

								# Also need to check if private entry to set flag accordingly (i.e. same as brand-new record)
								if oname.lower() == u'private' or len(fields) == 3:
									prvflag = True
									log.info("Registry for OUI %s is private, set private flag." % (oui))
						else:
							# Last record matches current record, so no change.
							# But if last record was a delete action then this is a re-appearance of the OUI and needs to be recorded as an add.
							if orec.getEvType() == 'delete':
								log.info("Records matched for %s but previous record was a delete action, re-adding entry" % (oui))
								drec.setEvType('add')
								delflag = False
					# No records found
					else:
						# Add this as a new record
						log.info("No existing records for OUI %s found, treating as new" % (oui))
						drec.setEvType('add')

						# If it's a private record, flag it as such
						if oname.lower() == u'private' or len(fields) == 3:
							prvflag = True
							log.info("Registry for OUI %s is private, set private flag." % (oui))

					# Update journal and flags if any changes were made
					if drec.getEvType() != False:
						dm.append(drec)
					if delflag != None: dm.setDeleted(oui, delflag)
					if prvflag != None: dm.setPrivate(oui, prvflag)

				# Finished processing file.
				fh.close()

				# -- Check for deleted/removed OUI entries --
				# Pull list of all OUIs in journal matching current OUI size being processed
				log.info("Checking for deleted OUI's in %s registry" % (fname))
				for o in dm.enumerate(sz = osz):
					# If an enumerated OUI isn't in our list of processed OUIs...
					 if o not in ouilist:
						# Differentiate between original IAB 36-bit OUI registry and newer MAM 36-bit OUI registry
						if fname == 'oui36.csv' and (o[:6] == '0050C2' or o[:6] == '40D855'):
							# The OUI isn't deleted, it's in another registry
							log.info("OUI %s is part of IAB registry, skipping." % (o))
							continue
						if fname == 'iab.csv' and (o[:6] != '0050C2' and o[:6] != '40D855'):
							# The OUI isn't deleted, it's in another registry
							log.info("OUI %s is NOT part of IAB registry, skipping." % (o))
							continue
						else:
							# Add a delete action record to the journal. Use the last available record for this OUI as a template.
							recs = dm.get(o)
							drec = recs[-1]
							drec.setEvType('delete')
							drec.setEvDate(last.strftime('%Y-%m-%d'))
							dm.append(drec)
							log.info("Added delete action for OUI %s to journal" % (o))

							# Mark this OUI as deleted in the journal
							dm.setDeleted(o, True)
							log.info("Set OUI %s deleted flag to true." % (o))
							
			# End of if-file-exists block

	prev = last
	last = last + datetime.timedelta(1)
	log.debug("last now %s" % (last))

### TODO: Generate final report (files processed, OUIs added/updated/removed, etc)

# Update last run date, re-write config
#cfg.set('dmimport', 'lastdate', today.strftime('%Y-%m-%d'))
cfg.set('dmimport', 'lastdate', last.strftime('%Y-%m-%d'))
with open(basedir + 'dmimport.cfg', 'wb') as fh:
	cfg.write(fh)
fh.close()

####

# End-of-line
