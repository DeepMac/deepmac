#!/usr/bin/perl

# Program: ouiarchive.pl
# Purpose : Grab latest copy of OUI.TXT from the IEEE website and store it in a directory named after the current date.
#			Also converts the text file into a comma-seperated value file.
#			The lack of perl modules is deliberate, to keep the code more portable.
#
# Updated : 2012-09-15 - Added lots of debugging code for completeness. Script now detects if file already exists for
#			current date. Also compares downloaded OUI.TXT to last downloaded copy and only keeps new download
#			if they differ. This will just save some space and keep things neat.
# Updated : 2013-01-29 - Just a few formatting tweaks and comments, nothing significant.
# Updated : 2013-04-18 - Fixed bug where checking for last directory in kb/ just grabbed the last file entry.
#			It now explicitly makes a list of directories, not files. May still mis-fire though so need to look
#			into using a more specific naming schema. Also added some more error checking.
# Updated : 2014-01-15 - Significant code changes to adapt to new IEEE registration standards (now 3 sizes of OUI
#			assignments), overhauling storage method of the registration files archive and  prepare for eventual
#			full reboot of DeepMac project.
# Updated : 2014-01-18 - Finalized changes by fixing a few bugs found in testing. Added status file for tracking the last
#			download date of a file. 
# Updated : 2015-01-09 - Added fix for when IEEE files sometimes have CRLF terminators. File downloaded is run through dos2unix
# Updated : 2015-05-05 - Fixed bug with checking for duplicate downloads. All the OUI files now contain a Generated: header
#			 (as of 5/20/14) which differs even when content doesn't. Using a new (kludgy) compare method.
# Updated : 2017-07-21 - Updated to change the way duplicates are detected, due to change in how IEEE generates their registry
#			 files.
# Updated : 2018-09-27 - Updated to use new URL's for registry files. Old URLs were still working but don't know for how long.

# Initialization and configuration
$DEBUG			= 1;
$SITEBASE		= 'YOUR-FULLY-QUALIFIED-SITE-BASE-HERE';
$OUI2CSV		= "$SITEBASE/reboot/oui2csv.pl";
$BASE			= "$SITEBASE/reboot/kb";
$TMPDIR			= "$SITEBASE/reboot/tmp";
$STATFILE		= "$BASE/.status";
$OUIURL{'oui.txt'}	= 'http://standards-oui.ieee.org/oui/oui.txt';
$OUIURL{'oui28.txt'}	= 'http://standards-oui.ieee.org/oui28/mam.txt';
$OUIURL{'oui36.txt'}	= 'http://standards-oui.ieee.org/oui36/oui36.txt';

debug("==- Starting a new run -==");

# Get current date, store in useful short-hand variables
(undef, undef, undef, $dd, $mm, $yy) = localtime();
$yy += 1900;
$mm = sprintf("%02d", ++$mm);
$dd = sprintf("%02d", $dd);
$today = "$yy$mm$dd";
$ouidir = "$BASE/$yy/$mm/$dd";

debug("today = $today", "ouidir = $ouidir");

# Read in status of last run if available
if (-f $STATFILE) {
	debug("Reading in status file $STATFILE");
	%Last = ();
	open(IN, $STATFILE);
	while (<IN>) {
		chomp();
		($key, $val) = split(/=/);
		if ($OUIURL{$key}) {
			$Last{$key} = $val;
			debug("key = $key", "val = $val");
		}
	}
	close(IN);
} else {
  debug("No status file exists!")
}

# Make sure we have a last run date for every kind of file we'll be checking
foreach $fname (keys %OUIURL) {
  if (! $Last{$fname}) {
	debug("No last date for $fname, initializing to $today");
	$Last{$fname} = $today;
  }
}

# Make sure storage directory exists. If not, create it.
if (! -d $ouidir) {
	$stat = system("mkdir -p $ouidir");
	if ($stat) {
		print "ERROR: Could not create directory $ouidir";
		debug("stat = $stat");
		exit 1;
	}
}

# Process each entry in the OUIURL hash in sequence
$updated = 0;
foreach $fname (keys %OUIURL) {
	# Initialize for this loop instance
	$url = $OUIURL{$fname};
	debug("fname = $fname", "url = $url");
	
	# Check to make sure there's not already something there
	debug("Checking to see if file already exists");
	if (-f "$ouidir/$fname") {
		debug("File already exists, nothing to do");
		next;
	}

	# Download the file for this iteration
	debug("Downloading $url");
	$stat = system("wget -q -O '$TMPDIR/$fname' $url");
	if ($stat) {
		print "ERROR: Problem downloading $fname\nStatus = $stat\n";

		# Jump to next file to check
		next;
	}

	# Run dos2unix on downloaded file to make sure any CRLF terminators are eliminated
	$stat = system("/usr/bin/dos2unix $TMPDIR/$fname");
	if ($stat) {
		print "WARNING: dos2unix returned error\n";
	}

	# Find the location of the last update of this file
	$date = $Last{$fname};
	$ldate = substr($date, 0, 4) . "/" . substr($date, 4, 2) . "/" . substr($date, 6, 2);
	debug("date = $date", "ldate = $ldate");

	# 2017-07-21: This check no longer works, as registry files are now internally arbitrarily
	# ordered and generated daily, even if no change in actual content
	#
	# Check to see if this is the same as the last file downloaded
#	debug("Checking to see if new file differs from previous one");
#	$stat = system("/usr/bin/diff -q $BASE/$ldate/$fname $TMPDIR/$fname > /dev/null");
#	$tmpstr = "\"/usr/bin/diff -q <(tail -n +2 $BASE/$ldate/$fname) <(tail -n +2 $TMPDIR/$fname) > /dev/null\"";
#	$stat = system("bash -c $tmpstr");
#	debug("stat = $stat");

	debug("Calling command to convert text to tab delimited format");
	$nfname = $fname;
	$nfname =~ s/\.txt$/\.csv/;
	$stat = system("$OUI2CSV $TMPDIR/$fname > $ouidir/$nfname");
	if ($stat) {
		print "ERROR: Problem converting $fname. Status = $stat\n";
	}

	# Check to see if newly created CSV file is different from previously generated file
	debug("Checking to see if new oui*.csv differs from previous one");
	$stat=system("/usr/bin/diff -q $BASE/$ldate/$nfname $ouidir/$nfname > /dev/null");
	debug("stat = $stat");

	# If files are the same nuke the download and quit, nothing else to do
	if ($stat == 0) {
		debug("New $fname matched previous version in $ldate (contextually)", "Deleting $TMPDIR/$fname and $ouidir/$nfname");
		unlink("$TMPDIR/$fname");
		unlink("$ouidir/$nfname");

		# Jump to next file to check
		next;
	} else {
		# Update status with new date
		$Last{$fname} = $today;
	}

	# Move downloaded file into storage directory
	$stat = rename("$TMPDIR/$fname", "$ouidir/$fname");
	if ($stat) {
		$updated = 1
	} else {
		print "ERROR: Couldn't move $TMPDIR/$fname to $ouidir\n";
		exit 1;
	}
}

# Check if there were updates or not
if ($updated) {
	# Write out updated status file
	debug("Writing new status file");
	open(OUT, ">$STATFILE" || die "Could not update $STATFILE");
	foreach $fname (keys %Last) {
		print OUT "$fname=$Last{$fname}\n";
	}
	close(OUT);
} else {
	# Remove the directory for today, not needed
	debug("No updates, attempting to remove $ouidir directory");
	$stat = rmdir($ouidir);
	debug("rmdir stat = $stat");
}


# All done
debug("Finished.");
exit 0;

#################################################################

sub debug(@) {
	# Only display debug messages if global flag is set
	if ($DEBUG) {
		my $dbg, $sub;

		# Output each parameter as its own message
		while ($dbg = shift) {
			# Fetch our caller subroutine name
			$sub = (caller(1))[3];

			# Print the debug message
			print "DEBUG-> $sub() $dbg\n";
		}
	}
}
