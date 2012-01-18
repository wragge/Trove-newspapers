#!/usr/bin/env python
import json
import datetime

import utilities
from utilities import get_url
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

class IssueError(Exception):
    pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()