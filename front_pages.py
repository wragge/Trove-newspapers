#!/usr/bin/env python
import datetime
import calendar
import os
import re
import json
import time
from urllib2 import Request, urlopen, URLError, HTTPError
import scrape
from BeautifulSoup import BeautifulSoup

from utilities import get_url
from issues import get_issue_url, IssueError, MONTH_ISSUES_URL
from titles import TITLES_URL, TITLE_HOLDINGS_URL

HARVEST_DIR = '/Users/tim/Documents/trove/'
TROVE_URL = 'http://trove.nla.gov.au'

def get_front_page_url(date, title_id):
    '''
    Gets the url of the front page given a date and a title

    >>> get_front_page_url(datetime.date(1925,1,1), '35')
    'http://trove.nla.gov.au/ndp/del/page/1223077'
    
    '''
    issue_url = get_issue_url(date, title_id)
    response = get_url(issue_url)
    return response.geturl()

def get_front_page_id(date, title_id):
    '''
    Gets the id of the front page given a date and a title.
    
    >>> get_front_page_id(datetime.date(1925,1,1), '35')
    '1223077'
    
    '''
    page_url = get_front_page_url(date, title_id)
    id = re.match(r'http:\/\/trove\.nla\.gov\.au\/ndp\/del\/page\/(\d+)', page_url).group(1)
    return id

def get_front_page_image(date, title_id, page_id=None):
    '''
    Retrieves jpg of front page. 
    '''
    if not page_id:
        page_id = get_front_page_id(date, title_id)
    image_url = '%s%s' % (scrape.IMAGE_PATH, page_id)
    response = get_url(image_url)
    return response.read()
    
def get_front_page_thumb(date, title_id, page_id=None):
    '''
    Retrieves teeny-weeny jpg of front page.
    '''
    if not page_id:
        page_id = get_front_page_id(date, title_id)
    image_url = '%s%s/thumb' % (scrape.IMAGE_PATH, page_id)
    response = get_url(image_url)
    return response.read()
    
def harvest_front_pages_text(start_year, end_year, title_id, start_month=None):
    '''
    Harvest and concatenate text content of all articles on front page.
    '''
    directory = '%s%s/text/' % (HARVEST_DIR, title_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if start_month:
        start_date = datetime.date(start_year, start_month, 1)
    else:
        start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    one_day = datetime.timedelta(days=1)
    this_day = start_date
    # Loop through each day in specified period 
    while this_day <= end_date:
        print 'Checking date: %s' % this_day.isoformat()
        filename = '%s%s-page1.txt' % (directory, this_day.isoformat())
        if not os.path.exists(filename):
            try:
                page_url = get_front_page_url(this_day, title_id)
            except IssueError:
                print "No Issue for this date"
            else:
                response = get_url(page_url)
                page = BeautifulSoup(response.read())
                articles = page.find('ul', 'articles').findAll('li')
                page_text = ''
                for article in articles:
                    article_url = TROVE_URL + article.h4.a['href']
                    response = get_url(article_url)
                    article_page = BeautifulSoup(response.read())
                    paras = article_page.find('div', 'ocr-text').findAll('p')
                    text = ''
                    for para in paras:
                        text += (' ').join([line.string for line in 
                                           para.findAll('span') if line.string]).strip()
                    text = text.replace('&nbsp;', ' ')
                    text = text.replace('  ', ' ')
                    page_text += text.encode('utf-8')
                print 'Saving: %s' % filename
                with open(filename, 'wb') as f:
                    f.write(page_text)            
        this_day += one_day
        time.sleep(1) 
    
def harvest_front_pages(start_year, end_year, title_id):
    '''
    Harvest images of front pages of the given title over the specified period.
    '''
    directory = '%s%s' % (HARVEST_DIR, title_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    one_day = datetime.timedelta(days=1)
    this_day = start_date
    # Loop through each day in specified period 
    while this_day <= end_date:
        print 'Checking date: %s' % this_day.isoformat()
        filename = '%s/%s.jpg' % (directory, this_day.isoformat())
        if not os.path.exists(filename):
            try:
                image = get_front_page_image(this_day, title_id)
            except IssueError:
                print 'No such issue.'
            else:
                print 'Saving: %s' % filename
                with open(filename, 'wb') as f:
                    f.write(image)            
        this_day += one_day
        time.sleep(1)

def harvest_front_pages_thumbs(start_year, end_year, title_id):
    '''
    Harvest thumbs of front pages of the given title over the specified period.
    '''
    directory = '%s%s/thumbs' % (HARVEST_DIR, title_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
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
            filename = '%s/%s-%s.jpg' % (directory, this_day.isoformat(), page_id)
            if not os.path.exists(filename):
                image = get_front_page_thumb(this_day, title_id, page_id)
                print 'Saving: %s' % filename
                with open(filename, 'wb') as f:
                    f.write(image)            
        this_day += one_day
        time.sleep(1)

def sample_front_pages():
    '''
    Retrieve a front page thumbnail for every title at monthly intervals.
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
            print 'Getting cover: %s' % first_issue_date.isoformat()
            page_id = get_front_page_id(first_issue_date, title['id'])
            filename = '%s/%s-%s.jpg' % (directory, first_issue_date.isoformat(), page_id)
            if not os.path.exists(filename):
                image = get_front_page_thumb(None, None, page_id)
                print 'Saving: %s' % filename
                with open(filename, 'wb') as f:
                    f.write(image) 

if __name__ == "__main__":
    import doctest
    doctest.testmod()