#!/usr/bin/perl
$|=1;

for ($rev=7805; $rev < 13359; $rev++) {
  $stat=system("svn export --username guest svn://svn.insecure.org/nmap/nmap-mac-prefixes -r$rev > /dev/null");
  if ($stat) {
    print "Possible error on downloading revision $rev\n";
    print "Stat = $stat\n";
    next;
  }

  # Check to see if this one is different than the previous one
  $stat=system("diff nmap-mac-prefixes nmap-mac-prefixes.prev --brief");
  if ($stat) {
    mkdir("/home/USERFIR/deepmac/nmaparchive/$rev");
    `cp nmap-mac-prefixes nmap-mac-prefixes.prev`;
    `mv nmap-mac-prefixes /home/USERDIR/deepmac/nmaparchive/$rev`;
    print "Archived revision $rev\n";
  }
}

print "Done!\n";
