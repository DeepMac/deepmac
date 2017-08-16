<?php
#  - Main Index page
#
# Author: Jeff Mercer <jedi@jedimercer.com>
# Written: 7/7/09
# Updated: 6/23/17
# Purpose: Provide main page with search form and general info.

include("bits/access.php");
$title="DeepMac - ALPHA";
include("bits/header.php");
?>

<CENTER>
<H1>DeepMac</H1>
<H2>OUI Search Interface</H2>
</CENTER>

<FONT SIZE=+1>
This is the alpha search interface to the DeepMac database, which itself is a grandiose project long in coming. 
For more details on what DeepMac is, see the <A HREF="http://www.jedimercer.com/archives/category/projects">project page</A>. 
For more inforation on what an OUI is, see the <A HREF="http://standards.ieee.org/regauth/registries.html">IEEE website</A> 
as well as <A HREF="http://en.wikipedia.org/wiki/Organizationally_Unique_Identifier">this Wikipedia article</A>.

A full code re-write in Python has been in the works since 2014, and the project is now <a href="https://github.com/DeepMac/deepmac/">available on github</a>, 
with both the original Perl code and the new Python code.
</FONT>
<P>

<DIV ALIGN=CENTER>
<HR WIDTH=35%>

<?php
# Attempt connection to database server
if (!($DBI=mysql_connect($DBHost, $DBUser, $DBPass))) {
  # Failed to connect, report error and quit.
  echo "<P>\n<B>Error!</B> Unable to connect to database server on $DBHost as $DBUser\n";
  include("footer.php");
  die();

  # Attempt selection of specified database instance
} elseif (!(mysql_select_db($DBName, $DBI))) {
  # Couldn't select the database, report error and quit.
  echo "<P>\n<B>Error!</B> Unable to select database $DBName on $DBHost\n";
  include("footer.php");
  die();
} else {
  # Everything checks out ok, so close the DB connection
  mysql_close($DBI);
}
?>

<EM>
Leave a field blank to match all records of that type.<BR>
All search terms are wildcarded automatically and are case-insensitive.<BR>
Use a percent sign (%) for wildcard matching inside a search term.
</EM>
<HR WIDTH=35%>

<TABLE FRAME=BORDER TITLE="DeepMac Search Form">
<CAPTION>DeepMac Search Form</CAPTION>

<FORM ACTION="search.php" METHOD=GET>

<TR>
<TD>Date:</TD>
<TD><INPUT TYPE="text" MAXLENGTH=10 SIZE=12 NAME="date">
<SUB><I>(YYYY-MM-DD, i.e. 2002-03-22)</I></SUB></TD>
</TR>

<TR>
<TD>MAC Address:</TD>
<TD><INPUT TYPE="text" MAXLENGTH=17 SIZE=19 NAME="macadd">
<SUB><I>(Seperators such as colons, hyphens or periods are optional)</I></SUB>
</TD>
</TR>

<TR>
<TD>Company Name:</TD>
<TD><INPUT TYPE="text" MAXLENGTH=128 SIZE=32 NAME="comp"></TD>
</TR>

<TR>
<TD>Device Type:</TD>
<TD><INPUT TYPE="text" MAXLENGTH=128 SIZE=32 NAME="dev"></TD>
</TR>

<TR>
<TD>Results per page:</TD>
<TD><INPUT TYPE="text" MAXLENGTH=4 SIZE=4 NAME="numresults" VALUE=50></TD>
</TR>

</TABLE>

<P>

<INPUT TYPE="reset" VALUE="Clear Form">
&nbsp;
<INPUT TYPE="submit" VALUE="Search">
</FORM>

<?php
include("bits/footer.php");
?>

</DIV>
</BODY>
</HTML>
