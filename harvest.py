'''
harvest.py
Created on 05/02/2011
@author: Tim Sherratt (tim@discontents.com.au)

Provides a harvester class that can be used to create data dumps from the 
Trove newspaper database.

USAGE:

query = 'http://trove.nla.gov.au/newspaper/result?exactPhrase=inclement+wragge'
filename = '/home/wragge/trove-output.csv'
text = True
pdf = True
harvester = harvest.TroveNewspapersHarvester()
harvester.harvest(query, filename, text, pdf)

(See bin/do_harvest.py for an example.)

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

from __future__ import with_statement #for Python 2.5
import csv
import os
import time
import string
from zipfile import ZipFile
from urllib2 import Request, urlopen, URLError, HTTPError

import scrape
    
class TroveNewspapersHarvester:
    '''
    Harvester class enabling you to retrieve the results of a
    Trove newspapers search, saving as a CSV file. You can also 
    choose to save zip files containing the text content of the articles 
    and/or pdfs of the articles.
    Usage:
    harvester = TroveNewspaperHarvester()
    harvester.harvest(query="[Trove search url]", filename="my.csv", text=True, pdf=True)
    '''
    def __init__(self):
        '''
        Set a few things up.
        '''
        self.gui = False
        self.completed = 0
        self.total = 0
        self.query = ''
        self.path = ''
        self.filename = ''
        self.csv_file = None
        self.text_zip_file = None
        self.pdf_zip_file = None
        self.zip_dir = ''
    
    def set_output_files(self, filename, text, pdf):
        '''
        Prepare the output files for the CSV, zipped text and zipped pdf.
        '''
        if not filename:
            filename = os.path.join(os.path.dirname(__file__), 
                                    'harvests', 'trove_newspapers_%s.csv' % int(time.time()))
        self.filename = filename
        if '.' in filename:
            self.path = filename[:string.rfind(filename, '.')]
        else:
            self.path = filename
        self.csv_file = csv.DictWriter(open(filename, 'ab'), extrasaction='ignore', 
                                       fieldnames=['id', 'title', 'url', 
                                                   'newspaper_title', 'newspaper_details', 
                                                   'newspaper_id', 'issue_date', 'page', 
                                                   'page_url','corrections','ftext'], 
                                                   dialect=csv.excel)
        print 'File created: %s' % filename
        # the path.exists check is necessary for Python 2.5
        if text: 
            if os.path.exists('%s_text.zip' % self.path):
                self.text_zip_file = ZipFile('%s_text.zip' % self.path, 'a')
            else:
                self.text_zip_file = ZipFile('%s_text.zip' % self.path, 'w')
            print 'File created: %s_text.zip' % self.path
        if pdf:
            if os.path.exists('%s_pdf.zip' % self.path):
                self.pdf_zip_file = ZipFile('%s_pdf.zip' % self.path, 'a')
            else:
                self.pdf_zip_file = ZipFile('%s_pdf.zip' % self.path, 'w')
            print 'File created: %s_pdf.zip' % self.path

    def harvest(self, query, filename=None, start=0, text=None, pdf=None, zip_dir='title', gui=None):
        '''
        Harvest the results of the supplied query, saving a CSV to the 
        (optional) filename. If no filename is given 
        '''
        self.query = query
        self.zip_dir = zip_dir
        self.set_output_files(filename, text, pdf)
        if start:
            self.completed = int(start)
        if gui:
            self.gui = gui
        page_url = '%s&s=%s' % (self.query, self.completed)
        news = scrape.TroveNewspapersClient()
        try:   
            news.search(url=page_url)
        except Exception, error:
            return self.harvest_failure(error)
        else:
            print 'Harvesting...'
            # Calculate number of pages
            total = int(string.replace(news.total_results, ',', ''))
            self.total = total
            if start:
                num_pages = (total - int(start)) / 20
            else:
                num_pages = total / 20
            page = 1
            # Write data from first page
            self.write_rows(news)
            # Loop over remaining pages
            while page <= num_pages:
                news.reset()
                news.tries = 10                
                page_url = '%s&s=%s' % (self.query, self.completed)
                #print page_url
                try:
                    news.search(url=page_url)
                except Exception, error:
                    return self.harvest_failure(error)
                else:
                    self.write_rows(news)
                    page += 1
        return {'status': 'success', 'error': None, 'total': self.total, 'completed': self.completed}
    
    def write_rows(self, news):
        '''
        Loop through a results page, retrieving and saving details for each article.
        '''
        results = news.results
        for result in results:
            if result['id']:
                news.reset()
                news.tries = 10
                # Get details of article
                try:
                    news.get_article(result['id'])
                except Exception, error:
                    return self.harvest_failure(error)
                else:
                    print '%s of %s -- %s' % (self.completed + 1, 
                                              self.total, 
                                              news.results['title'])
                    self.csv_file.writerow(news.results)
                    if self.text_zip_file or self.pdf_zip_file:
                        if self.zip_dir == 'year':
                            directory = str(news.results['issue_year'])
                            filename = '%s-%s-%s-%s-p%s' % (news.results['newspaper_id'], 
                                                            string.replace(news.results['newspaper_title'], ' ', '-'),
                                                            news.results['id'], 
                                                            string.replace(news.results['issue_date'], ' ', '-'), 
                                                            news.results['page'])
                        else:
                            directory = '%s-%s' % (news.results['newspaper_id'], 
                                                   string.replace(news.results['newspaper_title'], ' ', '-'))
                            filename = '%s-%s-p%s' % (news.results['id'], 
                                                      string.replace(news.results['issue_date'], ' ', '-'), 
                                                      news.results['page'])
                    if self.text_zip_file:
                        self.text_zip_file.writestr(('%s/%s.txt' % 
                                                     #encode added to filename because of problem with Python 2.5
                                                    (directory, filename)).encode('utf-8'), 
                                                    news.results['text'])
                    if self.pdf_zip_file:
                        pdf_url = 'http://trove.nla.gov.au/ndp/del/printArticlePdf/%s/3?print=n' % news.results['id']
                        try:
                            content = self.try_url(pdf_url)
                        except Exception, error:
                            return self.harvest_failure(error)
                        else:
                            #encode added to filename because of problem with Python 2.5
                            self.pdf_zip_file.writestr(('%s/%s.pdf' % 
                                                       (directory, filename)).encode('utf-8'), 
                                                       content.read())
                    time.sleep(1)
            self.completed += 1

                    
    def try_url(self, url):
        '''
        Set up a loop to retry downloads in the case of server (5xx) errors.
        '''
        success = False
        try_num = 1
        print 'Downloading pdf...'
        while success is False and try_num <= 10:
            if try_num > 1:
                print 'Download failed. Trying again in 10 seconds...'
                time.sleep(10)
            try:
                content = get_url(url)
            except ServerError:
                if try_num < 10:
                    try_num += 1
                    continue
                else:
                    raise
            except Exception:
                raise
            else:
                if content is not None:
                    success = True
                else:
                    if try_num == 10:
                        raise ServerError('Nothing was returned')
                    else:
                        try_num += 1
        return content

    def harvest_failure(self, error):
        '''
        Display information that should allow a failed harvest to be resumed.
        '''
        if self.gui:
            return {'status': 'error', 'error': error, 'total': self.total, 'completed': self.completed}
        else:
            print 'Harvest failed with error %s\n' % error
            if self.completed > 0:
                error_file = '%s_error.txt' % self.path
                error_message = 'Sorry your harvest failed.\n'
                error_message += 'The error was %s.\n\n' % error
                error_message += 'But never fear, you can easily restart your harvest.\n'
                error_message += 'Just set the "start" option in harvest.ini to %s,\n' % self.completed
                error_message += 'and then run "do_harvest" again.\n\n'
                error_message += 'Note that row number %s in the CSV file might be repeated.\n' % self.completed
                with open(error_file, 'w') as efile:
                    efile.write(error_message)
                print 'To resume harvest use the following command:\n'
                restart_message = 'python do_harvest.py -q "%s" -f "%s" -s %s' % (self.query, 
                                                                       self.filename, 
                                                                       self.completed)
                if self.text_zip_file:
                    restart_message += ' -t'
                if self.pdf_zip_file:
                    restart_message += ' -p'
                print restart_message
            return False

def get_url(url):
    '''
    Retrieve page.
    '''
    user_agent = 'Mozilla/5.0 (X11; Linux i686; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'
    headers = { 'User-Agent' : user_agent }
    req = Request(url, None, headers)
    try:
        response = urlopen(req)
    except HTTPError, error:
        if error.code >= 500:
            raise ServerError(error)
        else:
            raise
    except URLError, error:
        raise
    else:
        return response

class ServerError(Exception):
    pass

