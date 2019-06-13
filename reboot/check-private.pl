#!/usr/bin/perl

%delflag = {};
@unflagged = ();

# Load list of OUIs that are flagged private
open(IN, "private-flagged.txt");
while ($l = <IN>) {
  #./E8/18/63/8/.private
  chomp($l);

  @o = split('/', $l);
  if ($o[4] eq ".private") {
    $o[4] = "";
  }
  $x = sprintf("%s/%s/%s/%s", $o[1], $o[2], $o[3], $o[4]);

  $delflag{"$x"}++;
}
close(IN);

$sz = keys %delflag;
#print "delflag size = $sz\n";


# Process event log for private actions, find any NOT flagged
open(IN, "private-events.txt");
while ($l = <IN>) {
  chomp($l);

  #08/37/3D/records:                       "EventType": "delete",
  ($l) = split(':', $l);
  @o = split('/', $l);
  if ($o[3] eq "records") {
    $o[3] = "";
  }
  $x = sprintf("%s/%s/%s/%s", $o[0], $o[1], $o[2], $o[3]);

  if ($delflag{"$x"} == 0) {
    push(@unflagged, $x);
  }
}
close(IN);

# Pull event types from each OUI's records.
foreach $o (@unflagged) {
  @foo = ();
  open(IN, "$o/records");
  while ($l = <IN>) {
    if ($l =~ /OrgName/) {
      push(@foo, $l);
    }
  }
  close(IN);

  print "Events for OUI $o :\n";
  print $foo[-1];
  print "\n";
}
