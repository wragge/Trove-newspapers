===============================================================================
USING THE HARVESTER
===============================================================================

QUICK START:

1. Open the harvest.ini file in a text editor
2. Insert your harvest options as indicated and save the file.
3. Run do_harvest.py (double click in Windows)

IN MORE DETAIL

Using the do_harvest.py script you can initiate a harvest of Trove's newspaper database.

Depending on the configuration options you supply the script creates:

    * a CSV file containing the details of articles - [your filename]
    * a zip containing the text contents of articles - [your filename]_text.zip
    * a zip containing pdfs of articles - [your filename]_pdf.zip

The script receives its configuration values either from the command line, or by reading the
harvest.ini file.

SETTING HARVEST.INI
The harvest.ini file is well-documented, just enter the required values where indicated.

Once harvest.ini is set you can simply run do_harvest.py. In Windows you can just double click it. 
In Linux you'll probably need to cd to the directory containing the script and then run it from the 
terminal - python do_harvest.py

RUNNING FROM COMMAND LINE
The script can be run from the command line with the following arguments:

    -q (or --query) [full url of Trove newspapers search]
    -f (or --filename) [file and path name for the CSV output]
    -t (or --text) Create a zip file containing the text of articles
    -p (or --pdf) Create a zip file containing pdfs of articles
    -s (or --start) The result number to start at.
    
Example:

python do_harvest.py -q http://trove.nla.gov.au/newspaper/result?exactPhrase=inclement+wragge -f /home/wragge/trove-output.csv -t -p

If you're using Windows you'll have to make sure that the location of your Python 
installation is included in your Windows path variable.

RESTARTING A FAILED HARVEST

If for some reason a harvest fails, you can restart it where it left off.

In most cases, the script will write an error file ([your filename]_error.txt), 
explaining what happened and telling you what to do next.

This error file will include the number of the last completed record. 
Simply insert this as the 'start' value in harvest.ini (or include on the command line 
with the -s flag).

If for some reason the error file wasn't created. Open up the CSV file and look at the 
last row number. Use this value minus one as the start value for the script. This will 
ensure any text and pdf files are properly saved. You might also want to delete the last 
row of the CSV to avoid duplication.
want to delete the last row to
