<?php
#  - Header page
#
# Author: Jeff Mercer <jedi@jedimercer.com>
# Written: 7/7/09
# Updated: 11/20/14
# Purpose: This particular page is the header stub

header('Content-Type: text/html; charset=ISO-8859-1' );
header('Content-Language: en');
?>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">

<HTML>

<HEAD>
<?php
if (isset($title)) {
  echo "<TITLE>$title</TITLE>\n";
}
?>
<META name="description" content="Search engine for MAC addresses and Organizational Unit Identifiers (OUI), including addresses, creation date and device identification.">
<META name="keywords" content="MAC address,Media Access Control address,Media Access Control,Network Interface Card,physical network segment,Address Resolution Protocol,Organizational Unit Identifier,Individual Address Block,IEEE,IEEE Standards Association,mac address lookup,mac address vendor,mac vendor,mac lookup,browse mac address,address database">

</HEAD>

<BODY>
