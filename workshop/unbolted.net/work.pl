#!/usr/bin/perl
use DBD::mysql;

# Configuration and initialization
$DEBUG=1;
$ouicsv="/home/USERDIR/deepmac/kb/oui-dates.csv";
$dbname="deepmac";
$dbserver="";
$dbuser="DEEPMACUSER";
$dbpass="DEEPMACPASS";
$srcfile="oui-dates.csv";

# Connect to database
$dbh=DBI->connect("DBI:mysql:database=$dbname;host=$dbserver", $dbuser, $dbpass, {RaiseError => 1}) || die "Fatal DB error: $DBI->errstr";

# Read in OUI data that contains dates and add to database
&debug("Opening $ouicsv for reading");
open(IN, "clients.txt") || die "Could not open $ouicsv for reading";
while (<IN>) {
  # Extract fields from current line.
  chomp();

  # Update prefix entry
  $sql="UPDATE tb_OUI SET dev_id=4,dar=2,media_id=4 WHERE prefix=\"$_\"";
  $sth=$dbh->prepare($sql);
  $stat=$sth->execute;
  if (!$stat) {
    print "DB error - $sth->errstr\n";
    exit 1;
  }
}
close(IN);

# Finish up
$dbh->disconnect();

#################################################################################################################################

sub dosql {
  &debug("sql = $sql");

  $sth=$dbh->prepare($sql);
  if (!$sth) {
    return $dbh->errstr;
  }

  if (!$sth->execute) {
    return $sth->errstr;
  }

  return 0;
}

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
