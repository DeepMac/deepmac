#!/usr/bin/perl
open(IN, "oui.txt");
while (<IN>) {
  @fields=split(/\|/, $_);

  $prefix=$fields[0];

  $fields[0]=substr($prefix, 0, 2)."-".substr($prefix,2,2)."-".substr($prefix,4,2);

  $out=join("	", @fields);

  print $out;
}
close(IN);
