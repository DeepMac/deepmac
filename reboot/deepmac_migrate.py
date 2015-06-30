#!/usr/bin/python

# File   : deepmac-migrate.py
# Author : Jeff Mercer <jedi@jedimercer.com>
# Purpose: Do a (hopefully) one-time import of metadata from old Deepmac project to reboot.
# Written: 2015/05/05
# Updated: 2015/06/10

import sys
import os
import logging
import datetime
import ConfigParser
from deepmac_manager import dmManager
from deepmac_record_class import dmRecord

# Logging configuration
log = logging.getLogger('dm_migrate')
handler = logging.StreamHandler()
logformat = logging.Formatter("%(asctime)s - %(name)s %(levelname)s: %(message)s")
handler.setFormatter(logformat)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

# Initialization
basedir = '/home/USERDIR/deepmac/reboot/'
osz = 24
today = datetime.date.today()

log.debug("today = %s" % (today))
log.debug("osz = %d" % (osz))

# Establish a connection to the DeepMac repository
dm = dmManager('filesystem', basedir + 'journal', '')

# Open mysql-export.csv file, read into memory
fh = open('mysql-export.csv', 'r')
# Step through each entry in the file
for line in fh:
	fields = line.rstrip('\n').split('	')
	log.debug('line = %s' % (line))
	log.debug('fields size = %d' % (len(fields)))

	# Convert references to NULL to actual empty value
	for i in range(0,6):
		if fields[i] == 'NULL':
			fields[i] == ''

	# Extract metadata from this entry including OUI
	oui = fields[0]
	media = fields[3]
	device = fields[4]
	model = fields[5]
	notes = fields[6]

	log.debug("oui = %s" % (oui))
	log.debug("orgname = %s" % (fields[2]))

	# Calculate the mac1 and mac2 values for this OUI (full range)
	mac1 = oui + "000000"
	mac2 = oui + "FFFFFF"

	# Create a metadata record for this entry
	drec = dmRecord(rectype = 'metadata', source = 'DeepMac project', edate = today.strftime('%Y-%m-%d'), osize = osz, oui = oui, mac1 = mac1, mac2 = mac2, mtype = media, dtype = device, dmodel = model, note = notes)

	print drec.getOUI()

	# Check if any existing records exist for this OUI
	recs = dm.get(oui)
	if recs:
		log.debug("Existing records for OUI %s found" % (oui))
		drec.setEvType('add')

		# Update records
		dm.append(drec)
	# No records found
	else:
		log.debug("No existing records for OUI %s found, skipping" % (oui))
