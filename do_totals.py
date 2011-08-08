'''
do_totals.py
Created on 18/02/2011
@author: Tim Sherratt (tim@discontents.com.au)

SUMMARY

This script takes a Trove newspapers search and then for each year
extracts the number of articles matching the search and the proportion
of the total number of articles (ie search total / all articles total).

The results are saved as two JSON objects containing [year, value] pairs.
These can be easily imported into an HTML file and graphed using jqPlot
(http://www.jqplot.com/index.php).

USAGE

It is run from the command line with the following arguments:

    -q (or --query) [full url of Trove newspapers search]
    -f (or --filename) [file and path name for the js output, don't include file extension]
    

OUTPUT

filename-data.js file containing:

    var data = [[year1, value1], [year2, value2]...]
    var ratios = [[year1, value1], [year2, value2]...]

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
from __future__ import with_statement
import getopt
import sys
import string
import time
import re
import datetime
import os.path
try:
    import json
except ImportError:
    import simplejson as json

import scrape

def main(argv):
    '''
    Cycle through years obtaining totals and proportions.
    Save as JSON.
    '''
    try:
        opts, args = getopt.getopt(argv, "q:f:a", 
                                   ["query=", "filename=", "all"])
    except getopt.GetoptError:                                
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-q', '--query'):
            query = arg
        if opt in ('-f', '--filename'):
            filename = arg
        if opt in ('-a', '--all'):
            all = True
        else:
            all = False
    if not query:
        print 'You need to supply a word or phrase to search for.'
        sys.exit(2)
    filename = '%s-%s' % (filename, datetime.datetime.now().strftime('%Y-%m-%d'))
    news = scrape.TroveNewspapersClient()
    if re.search('&fromyyyy=(\d{4})', query):
        start = int(re.search('&fromyyyy=(\d{4})', query).group(1))
    else:
        start = 1803
    if re.search('&toyyyy=(\d{4})', query):
        end = int(re.search('&toyyyy=(\d{4})', query).group(1))
    else:
        end = 1954
    query = remove_dates_from_query(query)
    totals = {}
    ratios = {}
    for year in range(start, end + 1):
        this_query = '%s&fromyyyy=%s&toyyyy=%s' % (query, year, year)
        news.reset()
        news.tries = 10
        news.search(url=this_query)
        total = int(string.replace(news.total_results, ',', ''))
        totals[year] = total
        print '%s: %s' % (year, total)
        if total > 0:
            if all:
                this_query = 'http://trove.nla.gov.au/newspaper/result?fromyyyy=%s&toyyyy=%s' % (year, year)
            else:
                this_query = 'http://trove.nla.gov.au/newspaper/result?fromyyyy=%s&toyyyy=%s&l-category=Article|category:Article' % (year, year)
            news.reset()
            news.tries = 10
            news.search(url=this_query)
            total_all = int(string.replace(news.total_results, ',', ''))
            ratios[year] = float(total) / total_all
            print '%s total: %s' % (year, total_all)
            print 'Ratio: %s' % ratios[year]
        else:
            ratios[year] = 0
        time.sleep(1)
    var_name = os.path.basename(filename).replace(' ', '_').replace('-', '_')
    data = {}
    data['totals'] = [[year, total] for year, total in totals.items()]
    data['ratios'] = [[year, value] for year, value in ratios.items()]
    with open('%s-data.js' % filename, 'wb') as jsfile:
        jsfile.write('// Query: %s\n' % query)
        jsfile.write('// Date: %s\n' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        jsfile.write('%s = %s' % (var_name, json.dumps(data)))
        #jsfile.write('var %s_totals = %s;\n' % (var_name, json.dumps(total_list)))
        #jsfile.write('var %s_ratios = %s;\n' % (var_name, json.dumps(ratio_list)))
    print data

def remove_dates_from_query(query):
    '''
    Strip any existing date parameters from the query string.
    '''
    patterns = ['&fromdd=*\d{0,2}', '&frommm=*\d{0,2}', '&fromyyyy=*\d{0,4}',
                '&todd=*\d{0,2}', '&tomm=*\d{0,2}', '&toyyyy=*\d{0,4}']
    for pattern in patterns:
        query = re.sub(pattern, '', query)
    return query

if __name__ == "__main__":
    main(sys.argv[1:])