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
from urllib2 import URLError, HTTPError
from urllib import quote_plus

HARVEST_DIR = '/Users/tim/Documents/trove/'
TROVE_URL = 'http://trove.nla.gov.au'
TROVE_KEY = 'ei4napgems7bf1bo'
TROVE_API_URL = 'http://api.trove.nla.gov.au/result?zone=newspaper'
TROVE_TITLES_URL = 'http://api.trove.nla.gov.au/newspaper/titles/'
TROVE_TITLE_URL = 'http://api.trove.nla.gov.au/newspaper/title/'


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
    try:
        response = get_url(image_url)
    except HTTPError:
        return None
    else:
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
                if image:
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
        directory = '%ssamples/%s-%s' % (HARVEST_DIR, title['id'], title['name'])
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
                filename = '%s/%s-%s-%s-%s-p1.jpg' % (directory, first_issue_id, first_issue_date.isoformat(), page_id, size)
                if not os.path.exists(filename):
                    image = get_front_page_image(None, None, page_id, size=size)
                    if image:
                        print 'Saving: %s' % filename
                        with open(filename, 'wb') as f:
                            f.write(image)
                            
def get_front_page_totals():
    categories = {'Article': 'article', 'Advertising': 'advertising', 'Detailed lists, results, guides': 'lists', 'Family Notices': 'family', 'Literature': 'literature'}
    output_dir = os.path.join(HARVEST_DIR, 'frontpages')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)   
    #newspapers = []
    titles = []
    titles_file = os.path.join(output_dir, 'titles.js')
    results = json.load(get_url('%s?encoding=json&key=%s' % (TROVE_TITLES_URL, TROVE_KEY)))
    for newspaper_result in results['response']['records']['newspaper']:
        titles.append([newspaper_result['id'], newspaper_result['title']])
        with open(titles_file, 'wb') as titles_js:
            titles_js.write('var titles = %s;' % json.dumps(titles))
    for newspaper_result in results['response']['records']['newspaper']:
        id = newspaper_result['id']
        print 'Processing: %s' % newspaper_result['title']
        newspaper_dir = os.path.join(output_dir, id)
        if not os.path.exists(newspaper_dir):
            os.makedirs(newspaper_dir)
        years_file = os.path.join(newspaper_dir, 'year_totals.js')
        if not os.path.exists(years_file):
            issues_years = get_issue_totals_years(id)
            #newspaper['years'] = {}
            start_date = datetime.date(*map(int, re.split('[^\d]', newspaper_result['startDate'])))
            end_date = datetime.date(*map(int, re.split('[^\d]', newspaper_result['endDate'])))
            #for each year get month summaries
            year_totals = {}
            num_issues_year = {}
            for year in range(start_date.year, end_date.year+1):
                print 'Year: %s' % year
                year_totals[year] = {}
                num_issues_year[year] = 0
                num_issues_month = {}
                year_dir = os.path.join(newspaper_dir, str(year))
                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)
                '''
                # First we need to get the number of issues per month
                url = '%s%s/?encoding=json&key=%s&include=years&range=%s0101-%s1231' % (TROVE_TITLE_URL, newspaper['id'], TROVE_KEY, year, year)
                results = json.load(get_url(url))
                for year_issues in results['newspaper']['year']:
                    if year_issues['date'] == str(year):
                        issues_months = {}
                        for issue in year_issues['issue']:
                            issue_date = datetime.date(*map(int, re.split('[^\d]', issue['date'])))
                            try:
                                issues_months[issue_date.month] += 1
                            except KeyError:
                                issues_months[issue_date.month] = 1
                '''
                # Then we can get article details per month
                year_file = os.path.join(newspaper_dir, '%s.js' % year)
                if not os.path.exists(year_file):
                    print 'Getting article details...'
                    month_totals = {}
                    for month in range(1, 13):
                        month_totals[month] = {}
                        issue_totals = {}
                        article_list = {}
                        print 'Month: %s' % month
                        month_totals[month] = {}
                        url = '%s&encoding=json&key=%s&q=firstpageseq:1&l-title=%s&l-year=%s&l-month=%02d&reclevel=full&n=100' % (TROVE_API_URL, TROVE_KEY, id, year, month)
                        results = json.load(get_url(url))
                        total = int(results['response']['zone'][0]['records']['total'])
                        if total > 0:
                            articles = results['response']['zone'][0]['records']['article']
                            if total > 100:
                                n = 100
                                s = 0
                                while n == 100:
                                    next_url = '%s&s=%s' % (url, n+s)
                                    print next_url
                                    results = json.load(get_url(next_url))
                                    s = int(results['response']['zone'][0]['records']['s'])
                                    n = int(results['response']['zone'][0]['records']['n'])
                                    if n > 0:
                                        articles.extend(results['response']['zone'][0]['records']['article'])
                            for article in articles:
                                article_date = datetime.date(*map(int, re.split('[^\d]', article['date'])))
                                #Calculate totals for the month
                                if article['category'] != 'Other':
                                    cat = categories[article['category']]
                                    try:
                                        year_totals[year][cat]['total'] += 1
                                        year_totals[year][cat]['words'] += article['wordCount']
                                    except KeyError:
                                        year_totals[year][cat] = {}
                                        year_totals[year][cat]['total'] = 1
                                        year_totals[year][cat]['words'] = article['wordCount']
                                    try:
                                        month_totals[month][cat]['total'] += 1
                                        month_totals[month][cat]['words'] += article['wordCount']
                                    except KeyError:
                                        month_totals[month][cat] = {}
                                        month_totals[month][cat]['total'] = 1
                                        month_totals[month][cat]['words'] = article['wordCount']
                                    # Calculate totals for each issue
                                    try:
                                        issue_totals[article['date']][cat]['total'] += 1
                                        issue_totals[article['date']][cat]['words'] += article['wordCount']
                                    except KeyError:
                                        try:
                                            issue_totals[article['date']][cat] = {}
                                            issue_totals[article['date']][cat]['total'] = 1
                                            issue_totals[article['date']][cat]['words'] = article['wordCount']
                                        except KeyError:
                                            issue_totals[article['date']] = {}
                                            issue_totals[article['date']][cat] = {}
                                            issue_totals[article['date']][cat]['total'] = 1
                                            issue_totals[article['date']][cat]['words'] = article['wordCount']
                                    article_details = {'date': article['date'], 'heading': article['heading'], 'category': article['category'], 'word_count': article['wordCount'], 'url': article['identifier']}
                                    try:
                                        article_list[article['date']]['page_url'] = article['trovePageUrl']
                                    except KeyError:
                                        article_list[article['date']] = {}
                                        article_list[article['date']]['page_url'] = article['trovePageUrl']
                                    try:
                                        article_list[article['date']]['articles'].append(article_details)
                                    except KeyError:
                                        article_list[article['date']]['articles'] = []
                                        article_list[article['date']]['articles'].append(article_details)
                        for date, details in article_list.items():
                            with open(os.path.join(year_dir, '%s.js' % date), 'wb') as date_js:
                                json.dump(details, date_js)                
                        num_issues_month[month] = len(article_list)
                        num_issues_year[year] += len(article_list)
                        month_file = os.path.join(year_dir, '%s.js' % month)
                        with open(month_file, 'wb') as month_js:
                            json.dump(issue_totals, month_js);
                            '''
                            for category in categories.values():
                                total_list = []
                                words_list = []
                                for issue, values in issue_totals.items():
                                    try:
                                        total_list.append(('Date.UTC(%s, %s, %s)' % (issue.year, issue.month, issue.day), values[category]['total']))
                                        words_list.append(('Date.UTC(%s, %s, %s)' % (issue.year, issue.month, issue.day), values[category]['words']))
                                    except KeyError:
                                        total_list.append(('Date.UTC(%s, %s, %s)' % (issue.year, issue.month, issue.day), 0))
                                        words_list.append(('Date.UTC(%s, %s, %s)' % (issue.year, issue.month, issue.day), 0))
                                month_js.write('var %s_totals = %s;\n' % (category, json.dumps(total_list)))
                                month_js.write('var %s_words = %s;\n' % (category, json.dumps(words_list)))
                            month_js.write('var articles = %s;\n' % json.dumps(article_list))
                            '''
                    for month, values in month_totals.items():
                        num_issues = num_issues_month[month]
                        for cat, totals in values.items():
                            total = totals['total']
                            words = totals['words']
                            if total > 0: totals['total'] = float(total) / num_issues
                            if words > 0: totals['words'] = float(words) / num_issues
                    with open(year_file, 'wb') as year_js:
                        json.dump(month_totals, year_js)
                        '''
                        for category in categories.values():
                            total_list = []
                            words_list = []
                            for month, values in month_totals.items():
                                try:
                                    total = values[category]['total']
                                    words = values[category]['words']
                                except KeyError:
                                    total = 0
                                    words = 0
                                num_issues = num_issues_month[month]
                                if total > 0: total = float(total) / num_issues
                                if words > 0: words = float(words) / num_issues
                                total_list.append((month, total))
                                words_list.append((month, words))
                            year_js.write('var %s_totals = %s;\n' % (category, json.dumps(total_list))) 
                            year_js.write('var %s_words = %s;\n' % (category, json.dumps(words_list)))
                            '''
                                #print 'No %s' % category
                    # Then we can get articles by month facets
                    '''
                    print 'Getting totals by month...'
                    newspaper['years'][year]['months'] = {}
                    for category, label in categories.items():
                        #print url
                        url = '%s&encoding=json&key=%s&q=firstpageseq:1&l-title=%s&l-category=%s&l-year=%s&facet=month&n=0' % (TROVE_API_URL, TROVE_KEY, newspaper['id'], quote_plus(category), year)
                        results = json.load(get_url(url))
                        try:
                            months = results['response']['zone'][0]['facets']['facet']['term']
                        except TypeError:
                            months = []
                        for month_result in months:
                            month = int(month_result['search'])
                            count = float(month_result['count'])
                            if count != 0:
                                try:
                                    count = count / issues[month]
                                except KeyError:
                                    count = 0
                            try:
                                newspaper['years'][year]['months'][month][label]['total'] = count
                            except KeyError:
                                try:
                                    newspaper['years'][year]['months'][month][label] = {}
                                    newspaper['years'][year]['months'][month][label]['total'] = count
                                except KeyError:
                                    newspaper['years'][year]['months'][month] = {}
                                    newspaper['years'][year]['months'][month][label] = {}
                                    newspaper['years'][year]['months'][month][label]['total'] = count
                            try:
                                newspaper['years'][year]['months'][month][label]['words'] = month_totals[month][label]['words']
                            except KeyError:
                                newspaper['years'][year]['months'][month][label]['words'] = 0
                    year_file = os.path.join(newspaper_dir, '%s.js' % year)
                    print 'Writing %s' % year_file
                    with open(year_file, 'wb') as year_js:
                        for category in categories.values():
                            try:
                                totals = [(month, values[category]['total']) for month, values in newspaper['years'][year]['months'].items()]
                                print totals
                                year_js.write('var %s_totals = %s;\n' % (category, json.dumps(totals))) 
                                words = [(month, values[category]['words']) for month, values in newspaper['years'][year]['months'].items()]
                                year_js.write('var %s_words = %s;\n' % (category, json.dumps(words)))
                            except KeyError:
                                print 'No %s' % category
                # for each decade get year summaries
                print 'Getting totals by year...'
                start_decade = str(start_date.year)[:3]
                end_decade = str(end_date.year)[:3]
                for decade in range(int(start_decade), int(end_decade)+1):
                    for category, label in categories.items():
                        url = '%s&encoding=json&key=%s&q=firstpageseq:1&l-title=%s&l-category=%s&l-decade=%s&facet=year&n=0' % (TROVE_API_URL, TROVE_KEY, newspaper['id'], quote_plus(category), decade)
                        for num in range(0,10):
                            year = int('%s%s' % (decade, num))
                            try:
                                newspaper['years'][year][label] = {}
                            except KeyError:
                                newspaper['years'][year] = {}
                                newspaper['years'][year][label] = {}
                        results = json.load(get_url(url))
                        try:
                            years = results['response']['zone'][0]['facets']['facet']['term']
                        except TypeError:
                            years = []
                        for year_result in years:
                            year = int(year_result['display'])
                            count = float(year_result['count'])
                            if count != 0:
                                count = count / newspaper['issues'][year]
                            newspaper['years'][year][label]['total'] = count
                            try:
                                newspaper['years'][year][label]['words'] = year_totals[year][label]['words']
                            except KeyError:
                                newspaper['years'][year][label]['words'] = 0
                    print 'Writing %s' % years_file
                    with open(years_file, 'wb') as years_js:
                        for category in categories.values():
                            try:
                                totals = [(year, values[category]['total']) for year, values in newspaper['years'].items()]
                                years_js.write('var %s_totals = %s;\n' % (category, json.dumps(totals)))
                                words = [(year, values[category]['words']) for year, values in newspaper['years'].items()]
                                years_js.write('var %s_words = %s;\n' % (category, json.dumps(words)))
                            except KeyError:
                                print 'No %s' % category
        '''
            print 'Getting totals for this year...'
            for year, values in year_totals.items():
                        num_issues = num_issues_year[year]
                        for cat, totals in values.items():
                            total = totals['total']
                            words = totals['words']
                            if total > 0: totals['total'] = float(total) / num_issues
                            if words > 0: totals['words'] = float(words) / num_issues
            with open(years_file, 'wb') as years_js:
                json.dump(year_totals, years_js)
            '''
            with open(years_file, 'wb') as years_js:
                for category in categories.values():
                    total_list = []
                    words_list = []
                    for year, values in year_totals.items():
                        try:
                            total = values[category]['total']
                            words = values[category]['words']
                        except KeyError:
                            total = 0
                            words = 0
                        num_issues = num_issues_year[year]
                        if total > 0: total = float(total) / num_issues
                        if words > 0: words = float(words) / num_issues
                        total_list.append((year, total))
                        words_list.append((year, words))
                    years_js.write('var %s_totals = %s;\n' % (category, json.dumps(total_list))) 
                    years_js.write('var %s_words = %s;\n' % (category, json.dumps(words_list)))
            '''


def get_category_label(category):
    return category.split()[0].lower()

def get_issue_totals_years(title_id):
    url = '%s%s/?encoding=json&key=%s&include=years' % (TROVE_TITLE_URL, title_id, TROVE_KEY)
    print url
    results = json.load(get_url(url))
    issues = {}
    for year in results['newspaper']['year']:
        issues[int(year['date'])] = int(year['issuecount'])
    return issues
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()