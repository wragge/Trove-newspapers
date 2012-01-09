import csv
import datetime
import calendar
import os
import re
import json
import time
from urllib2 import Request, urlopen, URLError, HTTPError
import scrape
from BeautifulSoup import BeautifulSoup

from utilities import parse_date, format_date, find_duplicates

HARVEST_DIR = '/Users/tim/Documents/trove/'
TROVE_URL = 'http://trove.nla.gov.au'

def check_csv(file_name, year=None, exclude=[]):
    '''
    Check for missing editorials
    year: check every day in the specified year
    exclude: list of days to exclude from checking (eg. to exclude Sunday [6])
    '''
    articles = csv.reader(open(file_name, 'rb'), delimiter=',', quotechar='"')
    article_dates = []
    missing_dates = []
    for article in articles:
        # Get the date
        date = parse_date(article[6])
        article_dates.append(date)
    article_dates.sort()
    duplicates = find_duplicates(article_dates)
    print 'Duplicates: %s' % len(duplicates)
    if year:
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)
    else:
        start_date = article_dates[0]
        end_date = article_dates[-1]
    one_day = datetime.timedelta(days=1)
    this_day = start_date
    # Loop through each day in specified period to see if there's an article
    # If not, add to the missing_dates list.
    while this_day <= end_date:
        if this_day.weekday() not in exclude: #exclude Sunday
            if this_day not in article_dates:
                missing_dates.append(this_day)
        this_day += one_day
    print 'Missing: %s' % len(missing_dates)
    csv_out = csv.DictWriter(open(file_name, 'ab'), extrasaction='ignore', 
                                       fieldnames=['id', 'title', 'url', 
                                                   'newspaper_title', 'newspaper_details', 
                                                   'newspaper_id', 'issue_date', 'page', 
                                                   'page_url','corrections','ftext'], 
                                                   dialect=csv.excel)
    # Write a results file with nicely formatted dates
    with open(os.path.join(os.path.dirname(file_name), 'csv_check.html'), 'wb') as results:
        results.write('<html>\n<head>\n  <title>Results</title>\n</head>\n<body>')
        results.write('<h2>Duplicates:</h2>\n<table>\n')
        for dup in duplicates:
            results.write('<tr><td>%s</td><td><a href="%s">View issue</a></td></tr>\n' % (format_date(dup), get_issue_url(dup, '35')))
        results.write('</table>\n')
        results.write('<h2>Missing:</h2>\n<table>\n')
        for missing in missing_dates:
            results.write('<tr><td>%s</td><td><a href="%s">View issue</a></td></tr>\n' % (format_date(missing), get_issue_url(missing, '35')))
            csv_out.writerow({'issue_date': format_date(missing)})
        results.write('</table>\n')
        results.write('</body>\n</html>')
            
def get_issue_url(date, title_id):
    '''
    Gets the issue url given a title and date.
    '''
    year, month, day = date.timetuple()[:3]
    url = 'http://trove.nla.gov.au/ndp/del/titlesOverDates/%s/%02d' % (year, month)
    
    issues = json.load(urlopen(url))
    issue_id = None
    issue_url = None
    for issue in issues:
        if issue['t'] == title_id and int(issue['p']) == day:
            issue_id = issue['iss']
            break
    if issue_id:
        issue_url = 'http://trove.nla.gov.au/ndp/del/issue/%s' % issue_id
    else:
        raise IssueError
    return issue_url

def get_front_page_url(date, title_id):
    '''
    Gets the url of the front page given a date and a title.
    '''
    issue_url = get_issue_url(date, title_id)
    print issue_url
    response = get_url(issue_url)
    return response.geturl()

def get_front_page_id(date, title_id):
    '''
    Gets the id of the front page given a date and a title.
    '''
    page_url = get_front_page_url(date, title_id)
    print page_url
    id = re.match(r'http:\/\/trove\.nla\.gov\.au\/ndp\/del\/page\/(\d+)', page_url).group(1)
    return id

def get_front_page_image(date, title_id):
    page_id = get_front_page_id(date, title_id)
    image_url = '%s%s' % (scrape.IMAGE_PATH, page_id)
    response = get_url(image_url)
    return response.read()
    
def harvest_front_pages_text(start_year, end_year, title_id):
    directory = '%s%s/text/' % (HARVEST_DIR, title_id)
    if not os.path.exists(directory):
        os.makedirs(directory)
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

class IssueError(Exception):
    pass

class ServerError(Exception):
    pass
        
if __name__ == "__main__":
    #check_csv('/Users/tim/Documents/NMA/1913/smh-editorials.csv', year=1913, exclude=[6])
    
    #print get_front_page_id(datetime.date(1913, 1, 2), '35')
    harvest_front_pages_text(1920, 1920, '35')