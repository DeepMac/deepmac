#!/usr/bin/perl

# Program: ouiarchive.pl
# Purpose: Grab latest copy of OUI.TXT from the IEEE website and store it in a directory named after the current date.
#	   Also converts the text file into a comma-seperated value file.
#          The lack of perl modules is deliberate, to keep the code more portable.
# Updated: 2012-09-15 - Added lots of debugging code for completeness. Script now detects if file already exists for
#	   current date. Also compares downloaded OUI.TXT to last downloaded copy and only keeps new download
#	   if they differ. This will just save some space and keep things neat.
# Updated: 2013-01-29 - Just a few formatting tweaks and comments, nothing significant.
# Updated: 2013-04-18 - Fixed bug where checking for last directory in kb/ just grabbed the last file entry.
#          It now explicitly makes a list of directories, not files. May still mis-fire though so need to look
#          into using a more specific naming schema. Also added some more error checking.

# Initialization and configuration
$DEBUG=0;

$OUIURL='http://standards.ieee.org/regauth/oui/oui.txt';
$OUI2CSV='/home/USERDIR/deepmac/oui2csv.pl';
$BASE='/home/USERDIR/deepmac/kb';
@ls=();

debug("==- Starting a new run -==");

# Extract current date
(undef, undef, undef, $dd, $mm, $yy)=localtime();
$yy+=1900;
$mm=sprintf("%02d", ++$mm);
$dd=sprintf("%02d", $dd);
$today="$yy$mm$dd";

debug("today = $today", "Full path will be $BASE/$today/oui.txt");

# Check to make sure there's not already something there
debug("Checking to see if file already exists");
if (-f "$BASE/$today/oui.txt") {
  debug("File already exists, nothing to do");
  exit 0;
}

# Find date of last new download
opendir($DIR, $BASE) || die "Couldn't open $BASE directory for reading!";
while ($file=readdir($DIR)) {
  if (-d "$BASE/$file") { push(@ls, $file); }
}
closedir($DIR);

# Sort directory listing, then take last entry as last OUI update
@ls=sort(@ls);
$last=$ls[$#ls-1];
debug("last = $last");

# Make directory and download oui to it
debug("Making directory $BASE/$today");
mkdir("$BASE/$today") || die "Couldn't make $BASE/$today subdir!";

debug("Downloading $OUIURL");
$stat=system("wget -q -O '$BASE/$today/oui.txt' $OUIURL");
if ($stat) {
  print "Possible error downloading. Status = $stat\n";
  exit 1;
}

# Check to see if this is the same as the last file downloaded
debug("Checking to see if new oui.txt differs from previous one");
$stat=system("/usr/bin/diff -q $BASE/$last/oui.txt $BASE/$today/oui.txt > /dev/null");
debug("stat = $stat");

# If files are the same nuke the download and quit, nothing else to do
if ($stat == 0) {
  debug("New oui.txt matched previous.", "Deleting $BASE/$today/oui.txt");
  unlink("$BASE/$today/oui.txt");

  debug("Deleting $BASE/$today directory");
  rmdir("$BASE/$today");

  debug("Finished.");
  exit 0;
}

# File is different, so convert to tab delimited format
debug("Calling command to convert text to tab delimited format");
$stat=system("$OUI2CSV $BASE/$today/oui.txt > $BASE/$today/oui.csv");
if ($stat) {
  print "Possible error converting. Status = $stat\n";
  exit 1;
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
    while ($dbg=shift) {
      # Fetch our caller subroutine name
      $sub=(caller(1))[3];

      # Print the debug message
      print "DEBUG-> $sub() $dbg\n";
    }
  }
}
