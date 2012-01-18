import csv
import datetime
import calendar
import os
import re

import utilities
from utilities import parse_date, format_date, find_duplicates, get_titles

HARVEST_DIR = '/Users/tim/Documents/trove/'
TROVE_URL = 'http://trove.nla.gov.au'
YAHOO_ID = 'JAp9z33V34HzR4rvRaHUNsRuEadGdaoQlRWYwsObAM1YquTZ.m92jjrhx.X0mOro67op'

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

class ServerError(Exception):
    pass
        
if __name__ == "__main__":
    #check_csv('/Users/tim/Documents/NMA/1913/smh-editorials.csv', year=1913, exclude=[6])