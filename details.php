<?php
#  - Main Index page
#
# Author: Jeff Mercer <jedi@jedimercer.com>
# Written: 07/07/09
# Updated: 01/29/11
# Purpose: This particular page is for showing details on a mac address

# Change include search path to include the location of locally installed PEAR components
ini_set('include_path', ini_get('include_path').PATH_SEPARATOR."/home/riffer/pear/php");

# For doing rendering results of searches
require 'Structures/DataGrid.php';

# Comment out to disable error reporting
#	error_reporting(E_ALL);
#	ini_set('display_errors', 1);
#	PEAR::setErrorHandling(PEAR_ERROR_DIE); 

	error_reporting(E_NONE);

# Initialization and configuration
$title="DeepMac - OUI Search - Search Results";
include("bits/access.php");
include("bits/header.php");

# Simple function for callback from Structures_DataGrid_Column
function DMCompany($row) {
  extract($row);

  if ($record['address1']) { $add[]=$record['address1']; }
  if ($record['address2']) { $add[]=$record['address2']; }
  if ($record['address3']) { $add[]=$record['address3']; }
  if ($record['address4']) { $add[]=$record['address4']; }
  if ($record['address5']) { $add[]=$record['address5']; }

  if (! isset($add)) { $add[]="No address in database"; }
  $add=implode("<BR>", $add);

  return "{$record['compname']}<BR>$add<BR>{$record['country']}";
}

function DMOrgCompany($row) {
  extract($row);

  if ($record['orgaddress1']) { $add[]=$record['orgaddress1']; }
  if ($record['orgaddress2']) { $add[]=$record['orgaddress2']; }
  if ($record['orgaddress3']) { $add[]=$record['orgaddress3']; }
  if ($record['orgaddress4']) { $add[]=$record['orgaddress4']; }
  if ($record['orgaddress5']) { $add[]=$record['orgaddress5']; }

  if (! isset($add)) { $add[]="No address in database"; }
  $add=implode("<BR>", $add);

  return "{$record['orgcompname']}<BR>$add<BR>{$record['orgcountry']}";
}

# Get our passed-in parameters and sterilize against attempts to do SQL
# injection or other nefarious deeds.
$macadd		= escapeshellcmd(trim($_GET['macadd']));
$numresults	= escapeshellcmd(trim($_GET['numresults']));

#
# Do defaults for unspecified parameters
#

# Pagination setting defaults to 50 if it wasn't specified
if ($numresults == "" || empty($numresults)) { $numresults=50; }

## If no starting page given, start at 0
#if (empty($start)) { $start = 0; }

# Use wildcards for all of the optional fields if the field is blank
if ($macadd == "") { $macadd = '%'; }

#
# Perform data validation checks, abort if any of them fail.
#

# Check MAC address string length
if (strlen($macadd) > 17) {
  echo "OUI search parameter $macadd is too long.\n<P>\n";
  echo "<CENTER><A HREF=\"index.php\">New Search</A>";
  include("bits/footer.php");
  die();
}

# Make sure $numesults variable is numeric and a valid length
if (is_numeric($numresults) != 1 or strlen($numresults) > 4) {
  echo "Number of results per page value $numresults is invalid.\n<P>\n";
  echo "<CENTER><A HREF=\"index.php\">New Search</A>";
  include("bits/footer.php");
  die();
}

# Instantiate the DataGrid object
$DGrid=& new Structures_DataGrid($numresults);

# Define the database connection string
$DBConn=array("dsn" => "mysql://$DBUser:$DBPass@$DBHost/$DBName");

$DGrid->setDefaultSort(array('date'=>'ASC'));

# Finally, remove seperators from MAC field
$macadd=preg_replace("/[^A-Za-z0-9%]*/", "", $macadd);

##############################################################################

# Prep actual search query.
$SQLState = "
SELECT tb_OUI.prefix, tb_OUI.date, tb_company.compname, 
tb_company.address1, tb_company.address2,
tb_company.address3, tb_company.address4, 
tb_company.address5, tb_company.country, 
tb_company.orgcompname,
tb_company.orgaddress1, tb_company.orgaddress2, 
tb_company.orgaddress3, tb_company.orgaddress4, 
tb_company.orgaddress5, tb_company.orgcountry, 
tb_media.medianame, tb_device.devname, tb_model.modelname
  FROM tb_OUI
  LEFT JOIN tb_company
  ON tb_OUI.comp_id = tb_company.comp_id
  LEFT JOIN tb_media
  ON tb_OUI.media_id = tb_media.media_id
  LEFT JOIN tb_device
  ON tb_OUI.dev_id = tb_device.dev_id
  LEFT JOIN tb_model
  ON tb_OUI.model_id = tb_model.model_id
  WHERE tb_OUI.prefix like '%$macadd%'";


## Execute the search query
$sql_result=$DGrid->bind($SQLState, $DBConn);

# Print any binding/querying errors, if any
if (PEAR::isError($sql_result)) {
  echo "ERROR! Could not bind to database, or query failed! Original error message, if any, follows: ###> ";
  echo $sql_result->getMessage();
  echo " <### Giving up.";
  die;
}


# If there were no results, give an error
if ($DGrid->getRecordCount()==0) {
?>
<CENTER>No results were found for this search.<P>
<A HREF="index.php">New Search</A>
<?php
  include("bits/footer.php");
  die();
# Otherwise...
} else {
  # Start displaying the results
  $row_count=0;
?>

<CENTER>
<H1>Matching DeepMac Entries</H1>
<P>
<A HREF="index.php">New Search</A>
<P>

<?php
# Create our columns without speciality formatting
$DGrid->generateColumns(array(
  'prefix' => 'OUI',
  'date'   => 'Date',
));

# Manually add columns with special formatting
# And yes, this requires you specify a function name to do the formatting.
# And no, you can't just pass the field name into that function. Because this is the buttfuck way to do it
$DGrid->addColumn(new Structures_DataGrid_Column('Company', 'compname', 'compname', null, null, 'DMCompany()'));
$DGrid->addColumn(new Structures_DataGrid_Column('OrgCompany', 'orgcompname', 'orgcompname', null, null, 'DMOrgCompany()'));
$DGrid->addColumn(new Structures_DataGrid_Column("Media Type", "medianame", "medianame", array('align' => 'center'), null));
$DGrid->addColumn(new Structures_DataGrid_Column("Device Class", "devname", "devname", array('align' => 'center'), null));
$DGrid->addColumn(new Structures_DataGrid_Column("Device Model", "modelname", "modelname", array('align' => 'center'), null));

# Specify rendering options
$DGrid->setRendererOptions(array(
  'sortIconASC'         => '&uArr;',
  'sortIconDESC'        => '&dArr;',
  'headerAttributes'    => array('bgcolor' => '#E3E3E3'),
  'evenRowAttributes'   => array('bgcolor' => '#C6C6C6'),
));

# Specify border around table
$Rend=$DGrid->getRenderer();
$Rend->setTableAttribute('border', 1);

# Print the DataGrid with the default renderer (HTMLTable)
$Result=$DGrid->render(DATAGRID_RENDER_PAGER);
$Result=$DGrid->render();
$Result=$DGrid->render(DATAGRID_RENDER_PAGER);

?>

<P>
<A HREF="index.php">New Search</A>
</CENTER>

<?php
}

# End of the line
include("bits/footer.php");
?>
