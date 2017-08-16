#!/usr/bin/perl
use DBD::mysql;

# Program: stats.pl
# Purpose: Generate statistics about the DeepMac database and print to standard output

# Configuration and initialization
$CREDFILE='/home/USERDIR/deepmac/creds.txt';
$dbname="deepmac";
$dbserver="YOUR-MYSQL-DATABASE-SERVER-HERE";

# Open credentials file to read in database creds
open(IN, "$CREDFILE") || die "Couldn't open $CREDFILE";
$line=<IN>;
close(IN);
chomp($line);
($dbuser, $dbpass)=split(/	/, $line);

# Connect to database
$dbh=DBI->connect("DBI:mysql:database=$dbname;host=$dbserver", $dbuser, $dbpass, {RaiseError => 1}) || die "Fatal DB error: $DBI->errstr";

### Perform database queries to gather stats ###

#	- Count of device classes
$sql="SELECT COUNT(*) FROM tb_device";
$stat=&dosql();
$devcnt=$sth->fetchrow_array;

#	- Count of device models
$sql="SELECT COUNT(*) FROM tb_model";
$stat=&dosql();
$modcnt=$sth->fetchrow_array;

#	- Count of companies
$sql="SELECT COUNT(*) FROM tb_company";
$stat=&dosql();
$compcnt=$sth->fetchrow_array;

#	- Count of OUIs
$sql="SELECT COUNT(*) FROM tb_OUI";
$stat=&dosql();
$ouicnt=$sth->fetchrow_array;

#	- Count of Unique dates for OUIs
$sql="SELECT COUNT(DISTINCT(date)) FROM tb_OUI";
$stat=&dosql();
$datecnt=$sth->fetchrow_array;

#	- Number of OUIs per date
#	- Increase in OUIs per date from previous date
$sql="SELECT DISTINCT date FROM tb_OUI";
$stat=&dosql();
$dateref=$sth->fetchall_arrayref;
foreach $date (@$dateref) {
  $sql="SELECT COUNT(*) FROM tb_OUI WHERE date=\"@$date[0]\"";
  $stat=&dosql();
  $cnt=$sth->fetchrow_array;
  $OUIdates{@$date[0]}=$cnt;
}

#	- Total number of companies per date
$sql="SELECT DISTINCT date FROM tb_company";
$stat=&dosql();
$dateref=$sth->fetchall_arrayref;
foreach $date (@$dateref) {
  $sql="SELECT COUNT(*) FROM tb_company WHERE date=\"@$date[0]\"";
  $stat=&dosql();
  $cnt=$sth->fetchrow_array;
  $compdates{@$date[0]}=$cnt;
}

#	- Number of OUIs per unique device name
$sql="SELECT tb_device.devname, count(tb_OUI.dev_id) AS ouicnt
      FROM tb_device
      JOIN tb_OUI
      ON tb_device.dev_id = tb_OUI.dev_id
      GROUP BY tb_device.devname
      ORDER BY ouicnt DESC";
$stat=&dosql();
$topdev=$sth->fetchall_arrayref;

#	- Number of OUIs per company (top 20)
$sql="SELECT tb_company.compname, count(tb_OUI.comp_id) AS ouicnt
      FROM tb_company
      JOIN tb_OUI
      ON tb_company.comp_id = tb_OUI.comp_id
      GROUP BY tb_company.compname
      ORDER BY ouicnt DESC
      LIMIT 20";
$stat=&dosql();
$topcomp=$sth->fetchall_arrayref;

#	- Number of OUIs per organization country (top 20)
$sql="SELECT tb_company.country, count(tb_OUI.comp_id) AS ouicnt
      FROM tb_company
      JOIN tb_OUI
      ON tb_company.comp_id = tb_OUI.comp_id
      GROUP BY tb_company.country
      ORDER BY ouicnt DESC
      LIMIT 20";
$stat=&dosql();
$topnat=$sth->fetchall_arrayref;

# Finished querying database
$dbh->disconnect();

###########################################################################

print "Unique Table Entry Counts\n=========================\n";
print "Device Types = $devcnt\n";
print "Model Types  = $modcnt\n";
print "Companies    = $compcnt\n";
print "OUI Entries  = $ouicnt\n";
print "Dates        = $datecnt\n\n";

print "Top OUI Count by Device\n=========================================\n";
foreach $top (@$topdev) {
  print "@$top[0] has @$top[1] OUIs\n";
}
print "\n";

print "Top OUI Count by Company\n=========================================\n";
foreach $top (@$topcomp) {
  print "@$top[0] has @$top[1] OUIs\n";
}
print "\n";

print "Top OUI Count by Organization's Country\n=========================================\n";
foreach $top (@$topnat) {
  print "@$top[0] has @$top[1] OUIs\n";
}
print "\n";

print "OUI Counts by Date\n=========================================================\n";
foreach $key (sort {$a cmp $b} (keys %OUIdates)) {
  $totoui+=$OUIdates{$key};
  print "On $key, $OUIdates{$key} OUIs were added, for a total of $totoui\n";
}
print "\n";

# All done
exit 0;

#################################################################################################################################

sub dosql {
#  print "DEBUG: sql = $sql\n";

  $sth=$dbh->prepare($sql);
  if (!$sth) {
    print "DB error - $dbh->errstr\n";
    return $dbh->errstr;
  }

  if (!$sth->execute) {
    print "DB error - $sth->errstr\n";
    return $sth->errstr;
  }

  return 0;
}
