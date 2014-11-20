#!/usr/bin/perl

# Program: bacnet.pl
# Purpose: Take a file in the standard OUI.TXT format as distributed
#          by IEEE, and a file in the standard BACNet Vendor ID format
#	   as distributed by bacnet.org, and map BACNet vendor ID numbers
#	   to OUI numbers.
# Updated: 06/30/2010

use Data::Dumper;
use Geo::PostalAddress;

$DEBUG=1;

# Open OUI file and read into array
open(IN, $ARGV[0]) || die "Could not open OUI input file '$ARGV[0]' for reading";
@oui=<IN>;
close(IN);

# Open bacnet file and read into array
open(IN, $ARGV[1]) || die "Could not open BACNet input file '$ARGV[1]' for reading";
@bac=<IN>;
close(IN);

######
## Process OUI data into hash
######

# Take the element off the top to prime the loop
$line=shift(@oui);

# As long as we have data left...
while ($line) {
  # Look for beginning of new entry
  if ($line =~ /\(hex\)/) {
    # This is the first line of a OUI entry, extract the prefix and
    # company name
    ($prefix)=split(/ /, $line);
    (undef, undef, $comp)=split(/	/, $line);
    chomp($comp);

    # The rest of the data is pretty consistant, a series of entries until
    # we hit a blank line. The very next entry is always redundant, so skip
    $line=shift(@oui);

    # Is this a PRIVATE OUI entry?
    if ($comp eq "PRIVATE") {
      # Ok, just print what we've got and go to the next entry
      next;
    }

    # Read and store until we hit a NEW entry or end of file
    while ($line !~ /\(hex\)/ && defined($line)) {
      chomp($line=shift(@oui));
      push(@data, $line);
    }

    # Take the last two pieces off the end, not part of this entry
    pop(@data);
    pop(@data);

    # There can be anywhere from 1 to 6 lines for the company address, but the
    # last line is *usually* the country.
    $cn=pop(@data);
    $add1=$data[0];
    $add2=$data[1];
    $add3=$data[2];
    $add4=$data[3];
    $add5=$data[4];

    # Check for case where country was omitted from original oui.txt
    if ($cn =~ /\w+,?\s+[A-Z]{2}\s+[0-9]{5}/) {
      debug("Country '$cn' isn't a country");
      if ($add2 eq "") { $add2=$cn }
      elsif ($add3 eq "") { $add3=$cn }
      elsif ($add4 eq "") { $add4=$cn }
      elsif ($add5 eq "") { $add5=$cn }
      else {
        print "I got losted...\n";
        exit 1;
      }
      $cn="UNITED STATES";
    }

    # Eliminate excess whitespace
    $cn   =~ s/	//g;
    $add1 =~ s/	//g;
    $add2 =~ s/	//g;
    $add3 =~ s/	//g;
    $add4 =~ s/	//g;
    $add5 =~ s/	//g;

    # Convert to uppercase
    $comp =~ tr/a-z/A-Z/;
    $cn   =~ tr/a-z/A-Z/;
    $add1 =~ tr/a-z/A-Z/;
    $add2 =~ tr/a-z/A-Z/;
    $add3 =~ tr/a-z/A-Z/;
    $add4 =~ tr/a-z/A-Z/;
    $add5 =~ tr/a-z/A-Z/;

    # Store results into hash
    $ouidata{$prefix}=(
      "comp" => $comp,
      "add1" => $add1,
      "add2" => $add2,
      "add3" => $add3,
      "add4" => $add4,
      "add5" => $add5,
      "cn"   => $cn,
    );

    # Clear our temp store go to next entry
    @data=();
    next;
  }

  # Just go to next entry, these should be mostly blank lines
  $line=shift(@oui);
}


######
## Process BACNet data into hash
######

# Take the element off the top to prime the loop
$line=shift(@bac);

# As long as we have data left...
while ($line) {
  # Look for beginning of new entry
  if ( $line =~ /<TD>(\d+)<\/TD>/ ) {
    $id=$1;

    # Wipe any previous data
    $add1="";
    $add2="";
    $add3="";
    $add4="";
    $add5="";
    $cn="";

    # Get company name
    $line=shift(@bac);
    $line =~ /<TD>(.*)<\/TD>/;
    $comp=$1;

    # Skip contact name
    shift(@bac);

    # Get address line
    $line=shift(@bac);

    # Parse out address
    chomp($line);
    $line =~ s/<TD>//;
    $line =~ s/<\/TD>//;
    @data=split(/<BR>/, $line);

    # There can be anywhere from 1 to 3 lines for the company address, but the
    # last line is *usually* the country.
    $cn=pop(@data);
    $add1=$data[0];
    $add2=$data[1];
    $add3=$data[2];

    # Check for case where country was omitted from original oui.txt
    if ($cn =~ /\w+,?\s*[A-Z]{2}\s+\d+/) {
      $add2=$cn;
      $cn="UNITED STATES";
    }

    # Convert to uppercase
    $comp =~ tr/a-z/A-Z/;
    $cn   =~ tr/a-z/A-Z/;
    $add1 =~ tr/a-z/A-Z/;
    $add2 =~ tr/a-z/A-Z/;
    $add3 =~ tr/a-z/A-Z/;

    # Store results into hash
    $bacnet{$id}{comp}="$comp";
    $bacnet{$id}{add1}="$add1";
    $bacnet{$id}{add2}="$add2";
    $bacnet{$id}{add3}="$add3";
    $bacnet{$id}{cn}="$cn";

    # Clear our temp store go to next entry
    @data=();
    next;
  }

  # Just go to next entry
  $line=shift(@bac);
}

$bacsz=keys(%bacnet);
$ouisz=keys(%ouidata);

debug("bacnet hash size  = $bacsz");
debug("ouidata hash size = $ouisz");


######
## Perform mapping run
######
foreach $bac (keys %bacnet) {
#  debug("bac{comp} = $bacnet{$bac}{comp}");
  foreach $oui (keys %ouidata) {
    if ($bacnet{$bac}{add1} eq $ouidata{$oui}{add1}) {
       debug("OUI $oui has same company name as BACNet ID $bac");
    }
  }
}



############################################################

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
