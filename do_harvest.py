'''
do_harvest.py
Created on 05/02/2011
@author: Tim Sherratt (tim@discontents.com.au)

USAGE

This script initiates a harvest of Trove's newspaper database.
It can be run from the command line with the following arguments:

    -q (or --query) [full url of Trove newspapers search]
    -f (or --filename) [file and path name for the CSV output]
    -t (or --text) Create a zip file containing the text of articles
    -p (or --pdf) Create a zip file containing pdfs of articles
    -s (or --start) The result number to start at.
    
If run without any command line arguments, the script will look in 
config/harvest.ini for its configuration options.

Depending on the supplied configuration options the script creates:

    * a CSV file containing the details of articles - [your filename]
    * a zip containing the text contents of articles - [your filename]_text.zip
    * a zip containing pdfs of articles - [your filename]_pdf.zip

Copyright (C) 2011 Tim Sherratt
This file is part of the TroveNewspapers package.

The TroveNewspapers package is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The TroveNewspapers package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with the TroveNewspapers package. If not, see <http://www.gnu.org/licenses/>.
'''
import getopt
import sys
import ConfigParser

import harvest

CONFIG_FILE = 'config/harvest.ini'

def main(argv):
    # Look for user-defined values in a config file
    config = ConfigParser.SafeConfigParser({'query': '', 'filename': '',
                                            'start': 0, 
                                            'include-text': 'no', 
                                            'zip-directory-structure': 'title',
                                            'include-pdf': 'no'})
    config.read(CONFIG_FILE)
    query = config.get('harvest', 'query')
    filename = config.get('harvest', 'filename')
    start = config.getint('harvest', 'start')
    text = config.getboolean('harvest', 'include-text')
    zip_dir = config.get('harvest', 'zip-directory-structure')
    pdf = config.getboolean('harvest', 'include-pdf')
    # Look to see if there were any config values in the command line
    try:
        opts, args = getopt.getopt(argv, "q:f:s:d:tp", 
                                   ["query=", "filename=", "start=", "zipdir=", "text", "pdf"])
    except getopt.GetoptError:                                
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-q', '--query'):
            query = arg
        if opt in ('-f', '--file'):
            filename = arg
        if opt in ('-s', '--start'):
            start = arg      
        if opt in ('-t', '--text'):
            text = True
        if opt in ('-d', '--zipdir'):
            zip_dir = arg
        if opt in ('-p', '--pdf'):
            pdf = True
    if not query:
        print 'A Trove Newspapers search url is required.'
        sys.exit(2)
    harvester = harvest.TroveNewspapersHarvester()
    harvester.harvest(query, filename, start, text, pdf, zip_dir)
    
if __name__ == "__main__":
    main(sys.argv[1:])