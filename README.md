deepmac
=======

The DeepMac project is an attempt to archive indefinitely all OUI records and provide additional metadata related to OUI registrations. Data can be used by IT professionals for asset management and by security professionals for recon and assessment.

The code here is a long-term work-in-progress, with a focus on data and results over code quality, maintainability or efficiency. So no whinies, ;)
Original project started in 2008 and has moved slowly. A full redesign is in progress that focuses on a better way to record metadata about OUI registrations. Future features will allow for search engines that can find new metadata to add to the journals. See below for code overview.


Requirements
------------
 . A webserver with PHP and MySQL support
 . PHP 5.x (4.x may actually work fine)
 . Perl 5.x
 . MySQL 14 (older versions will almost definitely work)
 . Perl modules
	DBD::mysql
	Data::Dumper (opt)
	Geo::PostalAddress (opt)
 . PHP modules
	DB                                        1.7.13  stable
	DB_DataObject                             1.9.3   stable
	DB_Table                                  1.5.6   stable
	Date                                      1.4.7   stable
	HTML_Common                               1.2.5   stable
	HTML_QuickForm                            3.2.11  stable
	HTML_Table                                1.8.3   stable
	MDB2                                      2.4.1   stable
	MDB2_Driver_mysql                         1.4.1   stable
	PHPUnit                                   1.3.2   stable
	Pager                                     2.4.8   stable
	Structures_DataGrid                       0.9.0   beta
	Structures_DataGrid_DataSource_Array      0.1.4   beta
	Structures_DataGrid_DataSource_DB         0.1.1   beta
	Structures_DataGrid_DataSource_DBQuery    0.1.11  beta
	Structures_DataGrid_DataSource_DBTable    0.1.7   beta
	Structures_DataGrid_DataSource_DataObject 0.2.1   beta
	Structures_DataGrid_DataSource_MDB2       0.1.11  beta
	Structures_DataGrid_Renderer_Console      0.1.1   beta
	Structures_DataGrid_Renderer_HTMLSortForm 0.1.3   beta
	Structures_DataGrid_Renderer_HTMLTable    0.1.5   beta
	Structures_DataGrid_Renderer_Pager        0.1.3   beta
	Structures_Graph                          1.0.3   stable
	XML_Util                                  1.2.1   stable

Try and get all requirements together and functioning. Create a MySQL database to hold the original project data. You can initialize it using the dictionary files as a guide, or do a full import of the most recently available SQL dump.
Once a DB has been created and initialized, set-up credentials for it. A set of creds for read/write access to be used by the perl scripts for data loading or manual manipulation, and a read-only set to be used by the PHP search interface.
Add a file named "creds.txt" with the username and password to use for updating the DB. Format is a single line with "username	password" (tab whitespace).
Run and test the various perl scripts to make sure they execute and function correctly. You will need to fix hard-coded paths, put in the correct hostname for the DB backend, etc.
Establish cron jobs to run daily to perform the necessary archiving and updated tasks. Here's an example crontab:

	# Archive IEEE files
	00 01 * * *     ~USERDIR/deepmac/ouiarchive.pl >> ~USERDIR/archive.log
	15 01 * * *     ~USERDIR/deepmac/reboot/ouiarchive.pl >> ~USERDIR/deepmac/reboot/archive.log

	# Generate a master CSV files of dates associated with OUIs based on the archive
	00 02 * * *     ~USERDIR/deepmac/gen-ouidates.pl > ~USERDIR/deepmac/kb/oui-dates.csv

	# Run a database load, using the archive of IEEE OUI files
	00 03 * * *     ~USERDIR/deepmac/dbload.pl >> ~USERDIR/dbload.log

	# Generate some stats from the database for public consumption
	00 04 * * *     ~USERDIR/deepmac/stats.pl > ~USERDIR/deepmac/stats.txt

For the search interface, the PHP code will need to be executable by your webserver, so make sure you put together an appropriate and secure configuration. Deepmac has always used Apache on Linux but on a shared hosting provider.
Test the search interface to make sure it can access the DB and produce results.



Original Code
-------------
.
|-- bits		<-- Sub-dir for some PHP code
|-- dbload.pl		<-- Perl script to load MySQL database from a master OUI data file
|-- deepmacdict.html	\__ Database dictionary for MySQL back-end
|-- deepmacdict_files	/
|-- details.php		<-- PHP code to display detailed info on an OUi from backend
|-- dump.sh		<-- Simple Shell script to generate MySQL dumps (for cron)
|-- gen-ouidates.pl	<-- Perl script that generates a master OUI list with dates, from an archive of OUI files
|-- index.php		<-- Main PHP index page for Deepmac search
|-- oui2csv.pl		<-- Perl script to convert an IEEE-standard OUI text file to a tab-delimited format
|-- ouiarchive.pl	<-- Perl script to check for and archive IEEE OUI files (run as daily cron job)
|-- search.php		<-- PHP search code for DeepMac search interface
|-- sqldump.sql		<-- A MySQL dump of the database, includes metadata not found in the OUI files
|-- stats.pl		<-- Perl script to give some stats on the database backend
`-- workshop		<-- Sub-dir with one-offs
    |-- 20090427	<-- Restoration of a specific archived OUI dataset
    |-- bacnet-map.pl	<-- Non-working attempt to map bacnet IDs to OUI registrations
    |-- nmaparchive	<-- Archive of NMap SVN codes, for finding old OUI registry datasets
    |-- php		<-- PHP code archive
    `-- unbolted.net	<-- Archive of unbolted.net data related to Wireless profiles of OUI registrations


Project Reboot
--------------
|-- reboot
|   |-- deepmac_connector.py	<-- DeepMac connector class. Connect to a DeepMac journal (currently filesystem only)
|   |-- deepmac_import.py	<-- Python script to import OUI registry data into DeepMac journal
|   |-- deepmac_manager.py	<-- DeepMac manager class. Mange connections, journal operations, etc.
|   |-- deepmac_record_class.py	<-- DeepMac record class. Defines journal record format as an object, manipulates record entries, etc.
|   |-- dmimport.cfg		<-- Config file for deepmac_import.py
|   |-- gen-ouidates.pl		<-- Perl script that generates a master OUI list with dates, from an archive of OUI files
|   |-- journal			<-- Sub-dir for holding DeepMac journal entries (for filesystem mode)
|   |-- kb			<-- Sub-dir for holding IEEE OUI archive
|   |-- oui2csv.pl		<-- Perl script to convert an IEEE-standard OUI text file to a tab-delimited format
|   |-- ouiarchive.pl		<-- Perl script to check for and archive IEEE OUI files (run as daily cron job)
