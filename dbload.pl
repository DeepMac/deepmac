#!/usr/bin/perl
use DBD::mysql;
# Program: dbload.pl
# Purpose: Take a tab-delimited list of OUI data with dates (say, as created
#          by the generate.pl script) and load that data into a MySQL 
#          database that uses the DeepMac schema.
# Updated: 02/02/13

$|=1;

# Configuration and initialization
$DEBUG=0;
$KB='/home/USERDIR/deepmac/kb';
$OUICSV='/home/USERDIR/deepmac/kb/oui-dates.csv';
$CREDFILE='/home/USERDIR/deepmac/creds.txt';
$DBSERVER='';
$DBNAME='deepmac';
$date="";
$delta=0;
$cntComp=0;
$cntPrefix=0;

# Open credentials file to read in database creds
open(IN, "$CREDFILE") || die "Couldn't open $CREDFILE";
$line=<IN>;
close(IN);
chomp($line);
($dbuser, $dbpass)=split(/	/, $line);

# Determine the most recent OUI archive available, starting from the current
# date and working backwards.
while (! -f "$KB/$date/oui.csv") {
  (undef, undef, undef, $dd, $mm, $yy)=localtime(time-$delta);
  $yy+=1900;
  $mm=sprintf("%02d", ++$mm);
  $dd=sprintf("%02d", $dd);
  $date="$yy$mm$dd";
  $delta+=86400
}
$curoui="$KB/$date/oui.csv";

# Connect to database
$dbh=DBI->connect("DBI:mysql:database=$DBNAME;host=$DBSERVER", $dbuser, $dbpass, {RaiseError => 1}) || die "Fatal DB error: $DBI->errstr";

# Prepare SQL statements for inserting data
$sth_addcomp=$dbh->prepare('INSERT INTO tb_company (date, orgcompname, orgaddress1, orgaddress2, orgaddress3, orgaddress4, orgaddress5, orgcountry) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
$sth_addoui=$dbh->prepare('INSERT IGNORE INTO tb_OUI (prefix, comp_id, date) VALUES (?, ?, ?)');
$sth_upcomp=$dbh->prepare('UPDATE tb_company SET compname=?, address1=?, address2=?, address3=?, address4=?, address5=?, country=? WHERE comp_id=?');

# Prepare SQL statements for querying data
$sth_getpre=$dbh->prepare('SELECT prefix FROM tb_OUI WHERE prefix=?');
$sql='
SELECT comp_id FROM tb_company
WHERE 
(orgcompname=? AND orgaddress1=? AND orgaddress2=? AND orgaddress3=? AND orgcountry=?)
OR
(compname=? AND address1=? AND address2=? AND address3=? AND country=?)
';
$sth_getcomp=$dbh->prepare($sql);

# Read in OUI data that contains dates and add to database
Debug("Opening $OUICSV for reading");

open(IN, "$OUICSV") || die "Could not open $OUICSV for reading";
while (<IN>) {
  # Extract fields from current line.
  chomp();
  ($prefix, $date, $comp, $add1, $add2, $add3, $add4, $add5, $cnty)=split(/	/);

  # Clear redundant Country address lines if they exist
  if ($add5 == $cnty) { $add5=""; }
  if ($add4 == $cnty) { $add5=""; }
  if ($add3 == $cnty) { $add5=""; }

  # Normalize fields to prevent SQL errors
  $prefix =~ s/\-//g;

  Debug("prefix = $prefix", "date = $date", "comp = $comp", "add1 = $add1", "add2 = $add2", "add3 = $add3", "add4= $add4", "add5 = $add5", "cnty = $cnty");

  # Check if this prefix is already in the database.
  if (!$sth_getpre->execute($prefix)) {
    print "DB error - ${$sth_getpre->errstr}\n";
  }
  $ref=$sth_getpre->fetchall_arrayref;
  $rows=$sth_getpre->rows;
  Debug("rows = $rows");
  if ($rows > 0) {
    Debug("OUI $prefix already in database ($ref->[0][0]), skipping");
    next;
  }

  #####
  # Check if a company with this name already exists in the database
  #####
  Debug("Checking if company $comp already exists");

  # Perform SQL query to find matches
  $stat=$sth_getcomp->execute($comp, $add1, $add2, $add3, $cnty, $comp, $add1, $add2, $add3, $cnty);
  if (! defined($stat)) {
    print "DB error for sth_getcomp->execute - $sth_getcomp->errstr\n";
    exit 1;
  }

  # Check results to see if any matches
  $ref=$sth_getcomp->fetchall_arrayref;
  $rows=$sth_getcomp->rows;
  Debug("rows = $rows");

  # If we matched exactly one company...
  if ($rows == 1) {
    # Use this match's company ID
    $compid = $ref->[0][0];

    Debug("Company already exists. compid = $compid");
  } elsif ($rows == 0) {
    # We didn't match the company name, this is a new company
    Debug("No match for $comp, adding new entry");

    # Add new company
    $stat=$sth_addcomp->execute($date, $comp, $add1, $add2, $add3, $add4, $add5, $cnty);
    if (!$stat) {
      print "DB error for sth_addcomp->execute - $sth_addcomp->errstr\n";
      exit 1;
    }

    Debug("Retrieving last insert ID");

    # Get new company's id
    $sql="SELECT LAST_INSERT_ID()";
    $stat=&dosql();
    if ($stat) {
      print "DB error - $stat\n";
      exit 1;
    }
    @ary=$sth->fetchrow_array;
    $compid=$ary[0];

    $cntComp++;

    Debug("compid = $compid", "cntComp = $cntComp");
  } else {
    # More than one company matched. Woops!
    print "ERROR: Possible duplicate company entry.\n";
    $compid = $ref->[0][0];
#    exit 1;
  }

  #####
  # Add prefix entry with our company ID
  #####
  $stat=$sth_addoui->execute($prefix, $compid, $date);
  if (!$stat) {
    print "DB error for sth_addoui->execute - $sth_addoui->errstr\n";
    exit 1;
  }

  $cntPrefix++;    
  Debug("cntPrefix = $cntPrefix");
}
close(IN);

#####
# Read most current OUI for current company address info
#####
open(IN, $curoui) || die "Could not open $curoui for reading";

$sql="UPDATE tb_company SET compname=?, address1=?, address2=?, address3=?, address4=?, address5=?, country=? WHERE comp_id=?";
$sth_upcomp=$dbh->prepare($sql);

while (<IN>) {
  chomp();
  ($prefix, $comp, $add1, $add2, $add3, $add4, $add5, $cnty)=split(/	/);

  Debug("prefix = $prefix");

  # Normalize fields so as to eliminate SQL conflicts
  $prefix =~ s/\-//g;

  $sql="SELECT comp_id FROM tb_OUI WHERE prefix=\"$prefix\"";
  $stat=&dosql();
  if ($stat) {  
    print "DB error - $stat\n";
  }

  $ref=$sth->fetchall_arrayref;
  $rows=$sth->rows;
  if ($rows==1) {
    $compid=$ref->[0][0];
    Debug("compid = $compid");
    $stat=$sth_upcomp->execute($comp, $add1, $add2, $add3, $add4, $add5, $cnty, $compid);
    if (!$stat) {
      print "DB error - $sth_upcomp->errstr\n";
    }
  }
}
close(IN);

# Finish up
$dbh->disconnect();

print "Added $cntComp new companies to the database.\n";
print "Added $cntPrefix new OUIs to the database.\n";

# Generate a new mysqldump for public consumption
$stat = system("/usr/bin/mysqldump -u deepread -preadonly -h $DBSERVER deepmac > /home/USERDIR/deepmac/sqldump.sql");
if ($stat) {
  print "ERROR: Couldn't generate new mysqldump\n";
} else {
  print "Generated a new sqldump.sql file.\n";
}

#################################################################################################################################

sub dosql {
  Debug("sql = $sql");

  $sth=$dbh->prepare($sql);
  if (!$sth) {
    return $dbh->errstr;
  }

  if (!$sth->execute) {
    return $sth->errstr;
  }

  return 0;
}

sub Debug(@) {
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
