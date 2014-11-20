#!/usr/bin/perl

# Program: generate.pl
# Purpose: Take a directory of OUI.TXT files sorted by date, and generate a single tab-delimited list of the data. Dates for each OUI are
#	   obtained based on the directory the OUI first appears in.

# Configuration
$base='/home/USERDIR/deepmac/kb';
$DEBUG=0;

# Read in all directories in the specified directory. Sort the list.
opendir(DIR, $base) || die "Couldn't open $base";
@ouidirs=readdir(DIR);
closedir(DIR);
@ouidirs=sort(@ouidirs);

# For each directory...
foreach $dir (@ouidirs) {
  # If there's no OUI file, skip it
  if (! -f "$base/$dir/oui.csv") {
    Debug("Skipping $base/$dir, no oui.csv");
    next;
  }

  # Open the OUI file
  open(IN, "$base/$dir/oui.csv") || warn "Could not open $base/$dir/oui.csv";
  Debug("Processing $base/$dir/oui.csv");
  while (<IN>) {
    # Break up the data into fields, and copy into more sensible variable names
    chomp();
    @entry=split(/	/);
    # We are of course assuming the directory name is a date, in the format of
    # yyyymmdd or similar. If not, this will generate spooge.
    $date=substr($dir, 0, 8);

    # There can be anywhere from 1 to 6 lines for the company address, but the
    # last line is *usually* the country.
    $prefix=$entry[0];
    $comp=$entry[1];
    $add1=$entry[2];
    $add2=$entry[3];
    $add3=$entry[4];
    $add4=$entry[5];
    $add5=$entry[6];
    $cn  =$entry[7];

    # If this particular prefix does not already exist in our hash...
    if (! $oui{$prefix}{date}) {
      Debug("New prefix $entry[0]");
      # Add the data to the hash.
      $oui{$prefix}{date}=$date;
      $oui{$prefix}{comp}=$comp;
      $oui{$prefix}{add1}=$add1;
      $oui{$prefix}{add2}=$add2;
      $oui{$prefix}{add3}=$add3;
      $oui{$prefix}{add4}=$add4;
      $oui{$prefix}{add5}=$add5;
      $oui{$prefix}{country}=$cn;
    }
  }
  close(IN);
}

# Output the final OUI data, now with dates! Yay!
foreach $prefix (keys %oui) {
  print "$prefix	$oui{$prefix}{date}	$oui{$prefix}{comp}";
  print "	$oui{$prefix}{add1}	$oui{$prefix}{add2}	$oui{$prefix}{add3}";
  print "	$oui{$prefix}{add4}	$oui{$prefix}{add5}";
  print "	$oui{$prefix}{country}\n";
}

##########################################################################

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
