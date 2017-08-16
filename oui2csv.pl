#!/usr/bin/perl

# Program: oui2csv.pl
# Purpose: Take a file in the standard OUI.TXT format as distributed by IEEE, and output the data in a tabbed format
#	   with one entry per line. Can't use commas as separators, but tsv just doesn't convey the purpose.
# Updated: 2013-04-17 - Fixed issue that cropped up when oui.txt changed slightly. OUI is now extracted via regex.
# Updated: 2017-07-17 - Updated to sort the resulting CSV output

# Initialization and configuration
$DEBUG=0;

# Open OUI file and read into array
open(IN, $ARGV[0]) || die "Could not open input file '$ARGV[0]' for reading, or no file parameter passed";
@oui=<IN>;
close(IN);

# Take the element off the top to prime the loop
$line=shift(@oui);

# As long as we have data left...
while ($line) {
  # Look for beginning of new entry
  if ($line =~ /\(hex\)/) {
    debug("Found start of new entry");
    debug("line = $line");

    # This is the first line of a OUI entry, extract the prefix and company name.

    # Around Feb of 2013, format of oui.txt changed slightly. Instead of a OUI starting at the
    # first byte of a line it now has several spaces. So switched to regex.
#    ($prefix)=split(/ /, $line);
#    (undef, undef, $prefix)=split(/ /, $line);
    $line =~ m/\b((?:[ABCDEF0123456789]{2}\-){2}[ABCDEF0123456789]{2})\b/;
    $prefix=$1;

    (undef, undef, $comp)=split(/	/, $line);
    chomp($comp);

    debug("prefix = $prefix", "comp = $comp");

    # The rest of the data is pretty consistant, a series of entries until we hit a blank line.
    # The very next entry is always redundant, so skip
    $line=shift(@oui);

    # Is this a PRIVATE OUI entry?
    if ($comp eq "PRIVATE") {
      debug("Entry is marked PRIVATE");

      # Ok, just print what we've got and go to the next entry
      print "$prefix	$comp\n";
      next;
    }

    debug("Reading rest of entry");

    # Read and store until we hit a NEW entry or end of file
    while ($line !~ /\(hex\)/ && defined($line)) {
      chomp($line=shift(@oui));
      push(@data, $line);
    }

    # Take the last two pieces off the end, not part of this entry
    pop(@data);
    pop(@data);

    # There can be anywhere from 1 to 6 lines for the company address, but the last line is *usually* the country.
    $cn=pop(@data);
    $add1=$data[0];
    $add2=$data[1];
    $add3=$data[2];
    $add4=$data[3];
    $add5=$data[4];

    debug("Checking for missing country");

    # Check for case where country was omitted from original oui.txt
    if ($cn =~ /\w+,?\s+[A-Z]{2}\s+[0-9]{5}/) {
      debug("Country '$cn' isn't a country");
      if ($add2 eq "") { $add2=$cn }
      elsif ($add3 eq "") { $add3=$cn }
      elsif ($add4 eq "") { $add4=$cn }
      elsif ($add5 eq "") { $add5=$cn }
      else {
        debug("Logic for finding missing country amidst address data failed.", "Entry for $prefix may be longer than expected.");

        print "I got losted... :(\n";
        exit 1;
      }

      # Yep, if it wasn't included than it was good ol' USA!
      $cn="US";
    }

    # Eliminate excess whitespace
    $cn   =~ s/	//g;
    $add1 =~ s/	//g;
    $add2 =~ s/	//g;
    $add3 =~ s/	//g;
    $add4 =~ s/	//g;
    $add5 =~ s/	//g;

    # Ok, output what we have
#    print "$prefix	$comp	$add1	$add2	$add3	$add4	$add5	$cn\n";

    # Store this result in our results hash for later
    push(@results, "$prefix	$comp	$add1	$add2	$add3	$add4	$add5	$cn\n");

    # Clear our temp store go to next entry
    @data=();
    next;
  }

  # Just go to next entry, these should be mostly blank lines
  $line=shift(@oui);
}

# Sort the results and output them
@results = sort(@results);
print @results;

# All done
exit 0;

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
