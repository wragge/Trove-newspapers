#!/usr/bin/env python
import datetime
import os
import re
import json
import time
from BeautifulSoup import BeautifulSoup

import scrape
from utilities import get_url, convert_iso_to_datetime
from issues import get_issue_url, IssueError, MONTH_ISSUES_URL
from titles import TITLES_URL, TITLE_HOLDINGS_URL

HARVEST_DIR = '/Users/tim/Documents/trove/'
TROVE_URL = 'http://trove.nla.gov.au'

def get_front_page_url(date, title_id):
    '''
    Gets the url of the front page given a date and a title

    >>> get_front_page_url(datetime.date(1925,1,1), '35')
    'http://trove.nla.gov.au/ndp/del/page/1223077'
    
    >>> get_front_page_url('1925-01-01', '35')
    'http://trove.nla.gov.au/ndp/del/page/1223077'
    
    '''
    issue_url = get_issue_url(date, title_id)
    response = get_url(issue_url)
    return response.geturl()

def get_front_page_id(date, title_id, page_url=None):
    '''
    Gets the id of the front page given a date and a title.
    
    >>> get_front_page_id(datetime.date(1925,1,1), '35')
    '1223077'
    
    >>> get_front_page_id('1925-01-01', '35')
    '1223077'
    '''
    if not page_url:
        page_url = get_front_page_url(date, title_id)
    id = re.match(r'http:\/\/trove\.nla\.gov\.au\/ndp\/del\/page\/(\d+)', page_url).group(1)
    return id

def get_front_page_image(date, title_id, page_id=None, size='small'):
    '''
    Retrieves jpg of front page.
    Small images are about 300px wide.
    Thumbs are 150px high.  
    '''
    if not page_id:
        page_id = get_front_page_id(date, title_id)
    if size == 'small':
        image_url = '%s%s' % (scrape.IMAGE_PATH, page_id)
    elif size == 'thumb':
        image_url = '%s%s/thumb' % (scrape.IMAGE_PATH, page_id)
    response = get_url(image_url)
    return response.read()
    
def harvest_front_pages_text(start, end, title_id):
    '''
    Harvest and concatenate text content of all articles on front page.
    start and end are dates in ISO YYYY-MM-DD format, eg: '1857-02-04'
    
    >>> harvest_front_pages_text('1902-01-01','1902-01-01', '34')
    Checking date: 1902-01-01
    Saving: 1902-01-01-905929.txt
    '''
    directory = '%s%s/text/' % (HARVEST_DIR, title_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
    start_date = convert_iso_to_datetime(start)
    end_date = convert_iso_to_datetime(end)
    one_day = datetime.timedelta(days=1)
    this_day = start_date
    # Loop through each day in specified period 
    while this_day <= end_date:
        print 'Checking date: %s' % this_day.isoformat()
        try:
            page_url = get_front_page_url(this_day, title_id)
        except IssueError:
            print 'No such issue.'
        else:
            page_id = get_front_page_id(None, None, page_url)
            filename = '%s%s-%s.txt' % (directory, this_day.isoformat(), page_id)
            if not os.path.exists(filename):
                np = scrape.TroveNewspapersClient()
                np.extract_page_articles(page_url)
                articles = np.results
                page_text = ''
                for article in articles:
                    page_text += article['text']
                print 'Saving: %s' % os.path.basename(filename)
                with open(filename, 'wb') as f:
                    f.write(page_text)            
        this_day += one_day
        time.sleep(1) 
    
def harvest_front_pages(start, end, title_id, size='small'):
    '''
    Harvest images of front pages of the given title over the specified period.
    start and end are dates in ISO YYYY-MM-DD format, eg: '1857-02-04'
    
    >>> harvest_front_pages('1902-01-01','1902-01-01', '34')
    Checking date: 1902-01-01
    Saving: 1902-01-01-905929-small.jpg
    
    '''
    directory = '%s%s' % (HARVEST_DIR, title_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
    start_date = convert_iso_to_datetime(start)
    end_date = convert_iso_to_datetime(end)
    one_day = datetime.timedelta(days=1)
    this_day = start_date
    # Loop through each day in specified period 
    while this_day <= end_date:
        print 'Checking date: %s' % this_day.isoformat()
        try:
            page_id = get_front_page_id(this_day, title_id)
        except IssueError:
            print 'No such issue.'
        else:
            filename = '%s/%s-%s-%s.jpg' % (directory, this_day.isoformat(), page_id, size)
            if not os.path.exists(filename):
                image = get_front_page_image(None, None, page_id, size=size)
                print 'Saving: %s' % os.path.basename(filename)
                with open(filename, 'wb') as f:
                    f.write(image)            
        this_day += one_day
        time.sleep(1)

def sample_front_pages(size='thumb'):
    '''
    Retrieve a front page image for every title at monthly intervals.
    '''
    titles = json.load(get_url(TITLES_URL))
    for title in titles:
        print 'Processing: %s' % title['name']
        directory = '%ssamples/%s' % (HARVEST_DIR, title['id'])
        if not os.path.exists(directory):
            os.makedirs(directory)
        title_url = '%s%s' % (TITLE_HOLDINGS_URL, title['id'])
        holdings = json.load(get_url(title_url))
        for month in holdings:
            month_url = '%s%s/%s' % (MONTH_ISSUES_URL, month['y'], month['m'])
            issues = json.load(get_url(month_url))
            for issue in issues:
                if issue['t'] == title['id']:
                    first_issue = issue
                    break
            first_issue_id = first_issue['iss']
            first_issue_date = datetime.date(int(month['y']), int(month['m']), int(first_issue['p']))
            print 'Checking date: %s' % first_issue_date.isoformat()
            page_id = get_front_page_id(first_issue_date, title['id'])
            filename = '%s/%s-%s-%s.jpg' % (directory, first_issue_date.isoformat(), page_id, size)
            if not os.path.exists(filename):
                image = get_front_page_image(None, None, page_id, size=size)
                print 'Saving: %s' % filename
                with open(filename, 'wb') as f:
                    f.write(image) 

if __name__ == "__main__":
    import doctest
    doctest.testmod()