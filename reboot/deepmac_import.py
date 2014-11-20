#!/usr/bin/python

# File   : dmImport.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Import records from the IEEE registry archive into repository
# Written: 2014/06/11
# Updated: 2014/11/04

import os
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

dm = dmManager('filesystem', '/home/USERDIR/deepmac/reboot/journal', '')

cfg = ConfigParser.SafeConfigParser()
# TODO: If file doesn't exist, create it?
cfg.read('dmimport.cfg')

# TODO: If last isn't in file, create last with earliest available date in calendar (?)
last = cfg.get('dmimport', 'lastdate')
base = cfg.get('dmimport', 'basedir')
last = datetime.datetime.strptime(last, '%Y-%m-%d').date()
today = datetime.date.today()

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
		for fname in ('oui.csv', 'oui28.csv', 'oui36.csv'):
			# Check if this file exists
			if os.path.isfile(cwd + '/' + fname):
				# Open this file for processing
				try:
					fh = open(cwd + '/' + fname, 'r')
				except:
					# TODO: Better error handling
					raise

				# Determine OUI size being processed
				if fname == 'oui.csv':
					osz = 24
				elif fname == 'oui28.csv':
					osz = 28
				elif fname == 'oui36.csv':
					osz = 36
				log.debug("osz = %d" % (osz))

				# Read file and process for new/change/delete actions.
				log.debug("Processing %s/%s" % (cwd, fname))
				ouilist = []
				for line in fh:
					# TODO: Sanity-check line, make sure tab-delimited and the right number of fields, etc
					if line == "":
						continue

					fields = line.rstrip('\n').split('	')
					log.debug('line = %s' % (line))
					log.debug('fields size = %d' % (len(fields)))

#00-00-00	00-00-00	XEROX CORPORATION	M/S 105-50C	800 PHILLIPS ROAD	WEBSTER NY 14580				UNITED STATES
#74-19-F8	300000-3FFFFF	Essential Trading Systems Corp    9 Austin Drive        Marlborough CT 06447
#00-1B-C5	01D000-01DFFF	Rose + Herleth GbR        Wendenweg 17  Berlin  13595                           GERMANY
#00-1B-C5    013000-013FFF   Zamir Recognition Systems Ltd.    Manachat Tech Park 1/22       Jerusalem  96951                       ISRAEL

					oui = fields[0].translate(None, "-")
					if osz > 24:
						oui = oui + fields[1][0:(osz - 24) / 4]
					log.debug("oui = %s" % (oui))

					# Save all OUIs processed in a list for later use in deletion detection.
					ouilist.append(oui)

					if fields[2] == 'PRIVATE' or len(fields) == 3:
						drec = dmRecord(rectype = 'registry', source = 'IEEE', edate = last.strftime('%Y-%m-%d'), osize = osz, oui = oui, orgname=fields[2])
					else:
						if len(fields) < 8:
							country = "Unspecified"
						else:
							country = fields[8]

						oa = u'\n'.join(unicode(fields[3:7])).strip()
						if not oa:
							oa = 'Not listed in registry'

						drec = dmRecord(rectype = 'registry', source = 'IEEE', edate = last.strftime('%Y-%m-%d'), osize = osz, oui = oui, orgname=fields[2], orgadd=oa, orgcn=country)

						log.debug("orgname = %s" % (fields[2]))
						log.debug("oa = %s" % (oa))
						log.debug("type(orgname) = %s" % (type(fields[2])))
						log.debug("type(oa) = %s" % (type(oa)))

					# TODO: Check if record creation was successful or not.

					# Get any existing records for this entry's OUI
					recs = dm.get(oui)

					# If existing records found...
					if recs:
						log.debug("Existing records for OUI %s found" % (oui))
						# Check if most recent record matches this record
						# TODO: Fix this to only look at registry records, consider record type, etc.
						orec = recs[-1]

						log.debug("type(orec.rec['OrgName']) = %s" % (type(orec.rec['OrgName'])))
						log.debug("type(drec.rec['OrgName']) = %s" % (type(drec.rec['OrgName'])))
						if 'OrgAddress' in orec.rec:
							log.debug("type(orec.rec['OrgAddress']) = %s" % (type(orec.rec['OrgAddress'])))
						if 'OrgAddress' in drec.rec:
							log.debug("type(drec.rec['OrgAddress']) = %s" % (type(drec.rec['OrgAddress'])))

						# TODO: Add comparability to deepmac_record class??
						if not (orec.getOUI() == drec.getOUI() and orec.getOrgName() == drec.getOrgName() and orec.getOrgAddr() == drec.getOrgAddr() and \
							orec.getOrgCN() == drec.getOrgCN()):

							# Records differ, if previous record isn't a delete action then append this as a change record
							if orec.getEvType != 'del':
								# Add this as a change record type
								drec.setEvType('change')
								dm.append(drec)

								# Determine if this record switched to/from PRIVATE mode, flip flags accordingly
								if drec.getOrgName == 'PRIVATE' and orec.getOrgName != 'PRIVATE':
									# Record changed to private
									dm.setPrivate(fields[0], True)
								elif drec.getOrgName != 'PRIVATE' and orec.getOrgName == 'PRIVATE':
									# Record is no longer private
									dm.setPrivate(fields[0], False)
							# Last record was deletion of data, record this as a new add and turn off the deleted flag
							else:
								drec.setEvType('add')
								dm.append(drec)
								dm.setDeleted(fields[0], False)
						# Records matched
						else:
							# Last record matches current record, so no change. But if last record was a delete action
							# then this is a re-appearance of the OUI and needs to be recorded as an add
							if orec.getEvType == 'del':
								drec.setEvType('add')
								dm.append(drec)
								dm.setDeleted(fields[0], False)
					# No records found
					else:
						log.debug("No existing records for OUI %s found, treating as new" % (oui))
						# Add this as a new record
						drec.setEvType('add')
						dm.append(drec)
				fh.close()

			# End of if-file-exists block

		# TODO: Detect deletion events
		# 1) Determine which OUI size was processed based on file name (fname)
		# 2) Enumerate OUIs in repository that are not in a deleted state and match the OUI size from step 1
		#	2a) For each enumerated OUI, check if it is in ouilist array
		#		- If not, this is an OUI that has been deleted/removed. Mark it as deleted in repository
		#	2b) Process next enumerated OUI
		
		for o in dm.enumerate(sz = osz):
			if o not in ouilist:
				# OUI exists in current repository but not in our OUI list.
				dm.setDeleted(o, True)

	prev = last
	last = last + datetime.timedelta(1)
	log.debug("last now %s" % (last))

### Generate final report (files processed, OUIs added/updated/removed, etc)
### Update config with current date, write new config
# Update last run date
cfg.set('dmimport', 'lastdate', today.strftime('%Y-%m-%d'))

###################

# Step through repository by unique OUI that is not marked deleted, check if any are not in ouilist
#	Needs way to enumerate OUIs in repository


					# Deletions
### Move back in IEEE archive to find second most recent version of this CSV file
### Read in the previous .CSV file
### 	Parse a line from the file, extract OUI
###		Determine if this OUI is in OUI list created by first pass (above psuedocode)
###			If not, append this OUI as a Delete record type, set the DELETED flag
###		Process next line in file
