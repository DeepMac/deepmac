#!/usr/bin/python

# File   : dmImport.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Import records from the IEEE registry archive into repository
# Written: 2014/06/11
# Updated: 2017/08/14

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
log.setLevel(logging.DEBUG)

# Initialization
dupeoui = ('0001C8', '080030')
basedir = '/home/USERDIR/deepmac/reboot/'
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

# Loop through dates from last run to current date.
while last <= today:
	# Check if directory exists for this date
	cwd = base + last.strftime('/%Y/%m/%d')
	log.debug("cwd = %s" % (cwd))

	if os.path.isdir(cwd):
		# Cycle through possible OUI files here
		for fname in ('oui.csv', 'oui28.csv', 'oui36.csv', 'iab.csv'):
			# Check if this file exists
			if os.path.isfile(cwd + '/' + fname):
				# Open this file for processing
				try:
					fh = open(cwd + '/' + fname, 'r')
				except:
					# TODO: Better error reporting
					raise

				# Determine OUI size being processed
				if fname == 'oui.csv':
					osz = 24
				elif fname == 'oui28.csv':
					osz = 28
				elif fname == 'oui36.csv' or fname == 'iab.csv':
					osz = 36
				else:
					print "ERROR: Encountered unexpected import file. This shouldn't happen."
					exit()
				log.debug("osz = %d" % (osz))

				# Read CSV file and process for new/change/delete actions.
				log.debug("Processing %s/%s" % (cwd, fname))
				ouilist = []
				for line in fh:
					if line == "": continue

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
					if oname == u'PRIVATE' or len(fields) == 3:
						# Private registrations have no address or country of origin. Create a minimal record
						drec = dmRecord(rectype = u'registry', source = u'IEEE', edate = last.strftime('%Y-%m-%d').decode('utf8'), osize = osz, oui = oui, orgname=oname)
					else:
						log.debug("orgname = %s" % (fields[2]).encode('utf8'))

						# Not a private registration - Extract country
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
						drec = dmRecord(rectype = u'registry', source = u'IEEE', edate = last.strftime('%Y-%m-%d').decode('utf8'), osize = osz, oui = oui, orgname=oname, orgadd=oa, orgcn=country)

					# Check if any existing records exist for this OUI
					delflag = None
					prvflag = None
					recs = dm.get(oui)
					if recs:
						log.debug("Existing records for OUI %s found" % (oui))

						# Find the most recent registry record entry and extract it.
						# TODO: Potential failure here if loop never finds a registry record entry in the array
						# TODO: Re-write this, it's WRONG and logically flawed. Instead just start at end of array
						# TODO: and work backwords, stopping at the first registry entry
						for orec in reversed(recs):
							if orec.getType() == "registry":
								break

						# Check if any changes between most recent record in journal and our current record in hand
						if not (orec.getOrgName() == drec.getOrgName() and orec.getOrgAddr() == drec.getOrgAddr() and orec.getOrgCN() == drec.getOrgCN()):
							# Absurdly we must "whitelist" several OUIs as they are duplicated in the official registry files, :(
							if orec.getOUI() in dupeoui:
								log.debug("Skipping whitelisted OUI %s" % (oui))
								continue

							# Records differ - if previous record isn't a delete action then append this as a change record
							if orec.getEvType() != 'delete': drec.setEvType('change')
							else:
								# Last record was deletion of data, record this as a new add and turn off the deleted flag
								log.debug("Previously deleted OUI %s has been re-registered, changes detected." % (oui))
								drec.setEvType('add')
								delflag = False

							# Check if this OUI changed to/from PRIVATE, set flag accordingly.
							if drec.getOrgName() == u'PRIVATE' and orec.getOrgName() != u'PRIVATE':
								log.debug("OUI %s switched to private registry." % (oui))
								prvflag = True
							elif drec.getOrgName() != u'PRIVATE' and orec.getOrgName() == u'PRIVATE':
								log.debug("OUI %s switched to public registry." % (oui))
								prvflag = False
						else:
							# Last record matches current record, so no change. 
							# But if last record was a delete action then this is a re-appearance of the OUI and needs to be recorded as an add.
							# TODO: Fix this to use the actual flags that indicate a deleted status.
							if orec.getEvType() == 'delete':
								log.debug("Records matched for %s but previous record was a delete action, re-adding entry" % (oui))
								drec.setEvType('add')
								delflag = False
							# Nothing to record at all, skip to next entry
							else: continue
					# No records found
					else:
						# Add this as a new record
						log.debug("No existing records for OUI %s found, treating as new" % (oui))
						drec.setEvType('add')

						# If it's a private record, flag it as such
						if oname == u'PRIVATE' or len(fields) == 3:
							prvflag = True
							log.debug("Registry for OUI %s is private, set private flag." % (oui))

					# Update records and flags
					dm.append(drec)
					if delflag != None: dm.setDeleted(oui, delflag)
					if prvflag != None: dm.setPrivate(oui, prvflag)

				# Finished processing file.
				fh.close()

				# Check for deleted/removed OUI entries:
				# Pull list of all OUIs in journal matching current OUI size being processed
				log.debug("Checking for deleted OUI's in %s registry" % (fname))
				for o in dm.enumerate(sz = osz):
					# If an enumerated OUI isn't in our list of processed OUIs...
					 if o not in ouilist:
						# Differentiate between original IAB 36-bit OUI registry and newer MAM 36-bit OUI registry
						if fname == 'oui36.csv' and (o[:6] == '0050C2' or o[:6] == '40D855'):
							# The OUI isn't deleted, it's in another registry
							log.debug("OUI %s is part of IAB registry, skipping." % (o))
							continue
						if fname == 'iab.csv' and (o[:6] != '0050C2' and o[:6] != '40D855'):
							# The OUI isn't deleted, it's in another registry
							log.debug("OUI %s is NOT part of IAB registry, skipping." % (o))
							continue
						else:
							# Add a delete action record to the journal. Use the last available record for this
							# OUI as a template.
#							drec = dmRecord(rectype = 'registry', source = 'IEEE', edate = last.strftime('%Y-%m-%d'), osize = osz, oui = o)
							recs = dm.get(o)
							drec = recs[-1]
							drec.setEvType('delete')
							drec.setEvDate(last.strftime('%Y-%m-%d'))
							dm.append(drec)
							log.debug("Added delete action for OUI %s to journal" % (o))

							# Mark this OUI as deleted in the journal
							dm.setDeleted(o, True)
							log.debug("Set OUI %s deleted flag to true." % (o))
							
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
