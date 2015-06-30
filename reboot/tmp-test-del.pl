#!/usr/bin/perl

open(IN, "deleted.log");
while (<IN>) {
  chomp();
  $del{$_} = 1;
}
close(IN);

open(IN, "verify-deleted.log");
while ($fn = <IN>) {
  chomp($fn);
  if ($del{$fn}) {
    next;
  }

  open(IN2, "$fn/records") || die;
  @file = <IN2>;
  close(IN2);

  print "$fn	$file[$#$file]";
}
close(IN);
