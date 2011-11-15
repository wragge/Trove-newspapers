# TROVE TOOLS
## TroveNewspapers package

### Description

A series of tools to aid researchers using the National Library of Australia's 
Trove newspapers database.

### Contents:

*    scrape.py -- scraper client for retrieving and extracting data from the 
     Trove newspapers database.
*    harvest.py -- sets up a bulk download of articles matching a specified 
     search query
*    harvester.py -- a GUI for setting up and managing harvests
*    utilities.py -- used to generate lists of available newspaper titles
*    do_harvest.py -- script for initiating a new harvest
*    do_totals.py -- script to retrieve total numbers of articles matching a 
     query across time
*    do_summary.py -- script to retrieve total numbers of articles by state 
     and title
    +    config/harvest.ini -- config file for do_harvest.py
    +    data/titles_by_id.pck
    +    data/titles_by_state.pck
    
The files in the data directory are probably out of date, so use utilities.py 
to generate new ones if you need them.

### Dependencies:

*    BeautifulSoup
*    wxPython (for the GUI)

Copyright (C) 2011 Tim Sherratt (tim@discontents.com.au)
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