#!/usr/bin/env python
import json
import datetime
from BeautifulSoup import BeautifulSoup

import utilities
from utilities import get_url, parse_date
from titles import TITLES_URL

TITLE_HOLDINGS_URL = 'http://trove.nla.gov.au/ndp/del/yearsAndMonthsForTitle/'
MONTH_ISSUES_URL = 'http://trove.nla.gov.au/ndp/del/titlesOverDates/'
ISSUE_URL = 'http://trove.nla.gov.au/ndp/del/issue/'

def get_issue_url(date, title_id):
    '''
    Gets the issue url given a title and date.
    
    >>> get_issue_url(datetime.date(1925,1,1), '35')
    u'http://trove.nla.gov.au/ndp/del/issue/120168'
    
    '''
    if type(date) is datetime.date:
        year, month, day = date.timetuple()[:3]
    else:
        year, month, day = (int(num) for num in date.split('-'))
    url = '%s%s/%02d' % (MONTH_ISSUES_URL, year, month)
    issues = json.load(get_url(url))
    issue_id = None
    issue_url = None
    for issue in issues:
        if issue['t'] == title_id and int(issue['p']) == day:
            issue_id = issue['iss']
            break
    if issue_id:
        issue_url = '%s%s' % (ISSUE_URL, issue_id)
    else:
        raise IssueError
    return issue_url

def get_issues_by_titles(titles=None):
    '''
    For each title calculate the total number of issues on Trove, and the number of issues for each year.
    
    >>> get_issues_by_titles(['32'])
    The Hobart Town Mercury (Tas. : 1857): 142 issues
    [{'total_issues': 142, 'title_id': u'32', 'title_name': u'The Hobart Town Mercury (Tas. : 1857)', 'issues_by_year': {u'1857': 142}}]
    
    '''
    issue_totals = []
    title_list = json.load(get_url(TITLES_URL))
    for title in title_list:
        if title['id'] in titles:
            title_url = '%s%s' % (TITLE_HOLDINGS_URL, title['id'])
            holdings = json.load(get_url(title_url))
            current_year = holdings[0]['y']
            totals = {}
            total = 0
            for month in holdings:
                if current_year != month['y']:
                    current_year = month['y']
                try:
                    totals[current_year] += int(month['c'])
                except KeyError:
                    totals[current_year] = int(month['c'])
                total += int(month['c'])
            issue_totals.append({'title_id': title['id'], 'title_name': title['name'], 'total_issues': total, 'issues_by_year': totals})
            print '%s: %s issues' % (title['name'], total)
    return issue_totals

def get_title_issues(title, year):
    title_url = '%s%s' % (TITLE_HOLDINGS_URL, title)
    holdings = json.load(get_url(title_url))
    issues = []
    for month in holdings:
        if month['y'] == str(year): 
            month_url = '%s%s/%s' % (MONTH_ISSUES_URL, month['y'], month['m'])
            print month_url
            month_issues = json.load(get_url(month_url))
            for issue in month_issues:
                if issue['t'] == str(title):
                    issue_date = get_issue_date(issue['iss'])
                    issues.append({'id': issue['iss'], 'date': issue_date.isoformat()})
    return issues
                    
def get_issue_date(issue_id):
    issue_url = '%s%s' % (ISSUE_URL, issue_id)
    response = get_url(issue_url)
    page = BeautifulSoup(response.read())
    issue_date = page.find('div', 'issue').strong.string
    issue_datetime = parse_date(issue_date)
    return issue_datetime
                    
class IssueError(Exception):
    pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()