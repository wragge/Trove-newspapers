'''
do_totals.py
Created on 18/02/2011
@author: Tim Sherratt (tim@discontents.com.au)

============
SUMMARY
============

This script takes a Trove newspapers search and then for each year
extracts the number of articles matching the search and the proportion
of the total number of articles (ie search total / all articles total).

The results are saved in a JSON object which is automatically imported 
into an HTML file and graphed using HighCharts.

============
USAGE
============

do_titles.py [options] "your trove query url"

The url of your Trove query is the only required argument. The options allow you
to control the names and locations of your output files.

Options:

    -n (or --name) [The name of this series -- used for file names and to label 
                    the graph. Default is the search string. ]
    -p (or --pathname) [The full pathname of the directory/folder for your results.
                        Default is a 'graphs' sub-directory in the current directory.]
    -g (or --graph) [The name of an existing graph (html file) that you want to add 
                     this series to. Default is the series name.]
    -m (or --monthly) [Query at monthly intervals.]

To display multiple series in a single graph, simply use the 'graph' option to specify the
name of the html output file.

============
OUTPUT
============

The script creates a data file in the specified directory. The filename is based
on the supplied series name with an added date stamp, eg: 'your_series_name_2011_08_30.js'.

The data file creates a new graphData object and sets its name, query and data 
properties. This object is then added to a sources array.

The script also creates an html file in the same directory and with the same 
filename (except with an .html extension). This file automatically imports 
the data and displays a graph. You can manually customise the html if you want.

If you used the 'graph' parameter to supply the name of an existing html file,
the script will add the new data source to the existing graph. This makes it easy 
to build up comparisons.

The script also checks your results directory to see if it contains a 'css' and 
a 'scripts' directory. If they don't exist it will copy them across from the 
trovenewspapers source directory. (See REQUIREMENTS for an important note about the 
javascript files.)

============
REQUIREMENTS
============

The html file uses Highcharts to display the graph. The license conditions allow
Highcharts to be redistributed as part of non-commercial packages. However, Highcharts
is not free for commercial use. See the Highcharts website for details:

http://www.highcharts.com/

------------------------------------------------------------

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
from optparse import OptionParser
import getopt
import sys
import string
import time
import re
import datetime
import os
import os.path
import urlparse
try:
    from urlparse import parse_qs, parse_qsl
except ImportError:
# fall back for Python 2.5 
    from cgi import parse_qs, parse_qsl
import urllib
import shutil
try:
    import json
except ImportError:
    import simplejson as json

import scrape

ARTICLE_TYPES = {'Advertising|category:Advertising': 'advertising',
                 'Article|category:Article': 'news',
                 'Detailed+lists,+results,+guides|category:Detailed+lists,+results,+guides': 'lists',
                 'Family+Notices|category:Family+Notices': 'family',
                 'Literature|category:Literature': 'literature'}
                 
def main(argv):
    '''
    Cycle through years obtaining totals and proportions.
    Save as JSON.
    '''
    usage = 'usage: %prog [options] query'
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--n', dest='series_name', metavar='NAME',
                      help='name of the data series created from this query')
    parser.add_option('-d','--directory', dest='pathname', metavar='DIRECTORY',
                      help='directory in which to save graph and data')
    parser.add_option('-g','--graph', dest='graph',
                      help='name of graph (html) file for display')
    parser.add_option('-m', '--monthly', action="store_true", dest="monthly")
    (options, args) = parser.parse_args()
    if not args:
        # Exit if no query is supplied
        print 'You need to supply a query to harvest.'
        sys.exit(2)
    else:
        query = args[0]
    # If no series name is set use the keyword values from the query string
    if not options.series_name:
        query_parts = parse_qs(urlparse.urlsplit(query)[3])
        if 'q' in query_parts:
            series_name = query_parts['q'][0].replace('"', '').replace('+', ' ')
        elif 'exactPhrase' in query_parts:
            series_name = query_parts['exactPhrase'][0].replace('+', ' ')
        elif 'anyWords' in query_parts:
            series_name = query_parts['anyWords'][0].replace('+', ' ')
        else:
            series_name = 'Trove series'
    else:
        series_name = options.series_name
    # If no directory is set, use the current directory/graphs
    if options.pathname:
        pathname = options.pathname
    else:
        pathname = os.path.join(os.getcwd(), 'graphs')
    # Build output filenames including a time stamp
    var_name = '%s_%s' % (series_name.lower().replace(' ', '_').replace('-', '_').replace(',', '').replace("'", ''), datetime.datetime.now().strftime('%Y_%m_%d'))
    filename = os.path.join(pathname, var_name)
    # If no graph name is set, use the output filename
    if options.graph:
        graph_name = '%s.html' % (options.graph.lower().replace(' ', '_').replace('-', '_'))
    else:
        graph_name = '%s.html' % filename
    news = scrape.TroveNewspapersClient()
    # Look to see if a start year is set, otherwise start in 1803
    if re.search('&fromyyyy=(\d{4})', query):
        start = int(re.search('&fromyyyy=(\d{4})', query).group(1))
    else:
        start = 1803
    # Look to see if an end year is set, otherwise end in 1954
    if re.search('&toyyyy=(\d{4})', query):
        end = int(re.search('&toyyyy=(\d{4})', query).group(1))
    else:
        end = 1954
    # Remove dates from the query
    nodate_query = remove_dates_from_query(query)
    clean_query = remove_keywords_from_query(nodate_query)
    totals = []
    ratios = []
    data = {}
    for year in range(start, end + 1):
        print 'Year: %s' % year
        if options.monthly:
            months = {}
            for month in range(1, 13):
                print 'Month: %s' % month
                this_query = '%s&fromyyyy=%s&frommm=%02d&toyyyy=%s&tomm=%02d' % (nodate_query, year, month, year, month)
                total = get_total(news, this_query)
                if total > 0:
                    this_query = '%s&fromyyyy=%s&frommm=%02d&toyyyy=%s&tomm=%02d' % (clean_query, year, month, year, month)
                    ratio = get_ratio(news, this_query, total)
                else:
                    ratio = 0
                months[int(month)] = {'total': total, 'ratio': ratio}
            data[int(year)] = months
        else: 
            this_query = '%s&fromyyyy=%s&toyyyy=%s' % (nodate_query, year, year)
            total = get_total(news, this_query)
            # if total results > 0 get the total articles for the year
            if total > 0:
                this_query = '%s&fromyyyy=%s&toyyyy=%s' % (clean_query, year, year)
                ratio = get_ratio(news, this_query, total)
            else:
                ratio = 0
            data[int(year)] = {'total': total, 'ratio': ratio}
        time.sleep(1)
    # Write the data out to a js file
    if options.monthly:
        interval = 'month'
    else:
        interval = 'year'
    with open('%s.js' % filename, 'wb') as jsfile:
        jsfile.write('// Query: %s\n' % query)
        jsfile.write('// Date: %s\n' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        jsfile.write('var %s = new graphData();\n' % var_name)
        jsfile.write('%s.name = "%s";\n' % (var_name, series_name))
        jsfile.write('%s.interval = "%s";\n' % (var_name, interval))
        jsfile.write("%s.api_query = '%s';\n" % (var_name, parse_query(query)))
        jsfile.write('%s.data = %s;\n' % (var_name, json.dumps(data)))
        jsfile.write('dataSources.sources.push(%s);' % var_name)
    # Create the graph file
    create_html_page(pathname, graph_name, var_name, query, series_name)
    print data

def get_total(news, this_query):
    news.reset()
    news.tries = 10
    news.search(url=this_query)
    # Get the total results
    total = int(string.replace(news.total_results, ',', ''))
    print '    Query total: %s' % (total)
    return total
    
def get_ratio(news, this_query, total):
    news.reset()
    news.tries = 10
    news.search(url=this_query)
    total_all = int(string.replace(news.total_results, ',', ''))
    # Calculate the proportion
    ratio = float(total) / total_all
    print '    Article total: %s' % (total_all)
    print '    Ratio: %s' % ratio
    return ratio

def create_html_page(pathname, graph_name, var_name, query, series_name):
    '''
    Makes sure all the necessary scripts and styles are copied to the output
    directory. Inserts a reference to the data js file into the html output.
    '''
    css_dir = os.path.join(pathname, 'css')
    script_dir = os.path.join(pathname, 'js')
    html_path = os.path.join(pathname, graph_name)
    if not os.path.exists(css_dir):
        shutil.copytree('graphs/css', css_dir)
    if not os.path.exists(script_dir):
        shutil.copytree('graphs/js', script_dir)
    if not os.path.exists(html_path):
        html_in = 'graphs/graph.html'
    else:
        html_in = html_path
    with open(html_in, 'r') as html_file:
        html = html_file.read()
        html = html.replace('<!-- INSERT DATA HERE -->', '<!-- INSERT DATA HERE -->\n<script type="text/javascript" src="%s.js"></script>' % var_name)
        query_text = re.search(r'<!-- QUERY --><p>(.*)</p><!-- QUERYEND -->', html).group(1)
        if not query_text:
            query_text = 'Original query: <a href="%s">%s</a>' % (query, series_name)
        else:
            query_text = query_text.replace('query', 'queries')
            query_text += ', <a href="%s">%s</a>' % (query, series_name)
        html = re.sub(r'<!-- QUERY --><p>.*</p><!-- QUERYEND -->', '<!-- QUERY --><p>%s</p><!-- QUERYEND -->' % query_text, html)
        html = html.replace('<!-- DATE -->', '<p>Date harvested: %s\n' % datetime.datetime.now().strftime('%d %B %Y'))
    with open(html_path, 'w') as new_html:
        new_html.write(html);

def parse_query(query):
    '''
    Converts a Trove query string into a form that the API understands.
    '''
    params = []
    q_string = urlparse.urlparse(query)[4]
    q_params = parse_qs(q_string)
    if 'q' in q_params:
        params.append('all=%s' % q_params['q'][0])
    if 'anyWords' in q_params:
        params.append('any=%s' % q_params['anyWords'][0])
    if 'exactPhrase' in q_params:
        params.append('exact=%s' % q_params['exactPhrase'][0])
    if 'notWords' in q_params:
        params.append('exclude=%s' % q_params['notWords'][0])
    if 'l-category' in q_params:
        for type in q_params['l-category']:
            params.append('article_type=%s' % ARTICLE_TYPES[type])
    if 'l-title' in q_params:
        for title in q_params['l-title']:
            params.append('title=%s' % re.search(r'.*?(\d+)$', title).group(1))
    api_query = ('&').join(params)
    return api_query

def remove_keywords_from_query(url):
    '''
    Removes search keywords from a query string.
    '''
    parts = urlparse.urlparse(url)
    query = parse_qsl(parts[4])
    params = []
    for param in query:
        if param[0] in ['q','anyWords', 'exactPhrase', 'notWords']:
            params.append('%s=' % param[0])
        else:
            params.append('%s=%s' % (param[0], urllib.quote_plus(param[1])))
    cleaned_query = ('&').join(params)
    cleaned_url = urlparse.urlunparse((parts[0], parts[1], parts[2], parts[3], cleaned_query, parts[5]))
    return cleaned_url

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
