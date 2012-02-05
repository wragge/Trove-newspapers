from __future__ import division
import csv
import datetime
import calendar
import os
import re
from urllib import quote_plus
import json
import nltk
from nltk.corpus import wordnet as wn
import string

import utilities
from utilities import parse_date, format_date, find_duplicates, get_titles, clean_filename
from harvest import TroveNewspapersHarvester
from titles import get_titles_by_year
from issues import get_title_issues

HARVEST_DIR = '/Users/tim/Documents/trove/'
TROVE_URL = 'http://trove.nla.gov.au'
YAHOO_ID = 'JAp9z33V34HzR4rvRaHUNsRuEadGdaoQlRWYwsObAM1YquTZ.m92jjrhx.X0mOro67op'
NMA_FOLDER = '/Users/tim/Documents/NMA/1913/editorials/titles'

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
        
def check_all_editorials(csv_folder, year):
    # Get files excluding silly Apple dot files
    csv_files = [csv for csv in os.listdir(csv_folder) if csv[0] != '.' and csv != 'json']
    totals = []
    for csv_file in csv_files:
        results = check_editorial(os.path.join(NMA_FOLDER, csv_file), year)
        total_article_dates = results['issues'] - len(results['missing'])
        print '%s: %s%%' % (results['name'], float(total_article_dates)/results['issues'] * 100)
        totals.append({'id': results['id'],
                       'name': results['name'],
                       'articles': len(results['articles']),
                       'issues': results['issues'],
                       'odd': len(results['odd']),
                       'short': len(results['short']),
                       'long': len(results['long']),
                       'missing': len(results['missing']),
                       'duplicates': len(results['duplicates'])
                        })
    json_file = '%s/json/%s-totals.js' % (NMA_FOLDER, year)
    print json_file
    with open(json_file, 'wb') as json_data:
        json.dump(totals, json_data, indent=2)
    return totals
        
    
def check_editorial(csv_file, year):
    print csv_file
    articles = csv.reader(open(csv_file, 'rb'), delimiter=',', quotechar='"')
    # Things to check:
    #   Duplicate dates
    #   Number of words
    #   Page Number
    #   Missing -- article for each issue
    title_id = None
    title_name = None
    article_count = 0
    article_dates = []
    articles_filtered = []
    odd_pages = []
    short_articles = []
    long_articles = []
    missing_dates = []
    for article in articles:
        article_count += 1
        if not title_id: title_id = article[5]
        if not title_name: title_name = article[3]
        # Get the date
        try:
            page_number = int(article[7])
        except ValueError:
            page_number = int(re.search(r'(\d+)', article[7]).group(1))
        article_url = article[2]
        article_title = article[1]
        article_date = parse_date(article[6])
        text = article[10]
        word_count = len(text.split())
        # Check if page number is odd or even
        if page_number % 2: 
            odd_pages.append({'url': article_url,
                              'title': article_title,
                              'date': article_date.isoformat(),
                              'page': page_number,
                              'length': word_count})
        else:
            if word_count < 100:
                short_articles.append({'url': article_url,
                              'title': article_title,
                              'date': article_date.isoformat(),
                              'page': page_number,
                              'length': word_count})
            elif word_count > 1500:
                long_articles.append({'url': article_url,
                              'title': article_title,
                              'date': article_date.isoformat(),
                              'page': page_number,
                              'length': word_count})
            else:
                article_dates.append(article_date.isoformat())
                articles_filtered.append({'url': article_url,
                              'title': article_title,
                              'date': article_date.isoformat(),
                              'page': page_number,
                              'length': word_count})
    # Return duplicates
    duplicate_dates = sorted(set(find_duplicates(article_dates)))
    # Remove duplicates
    article_dates = sorted(set(article_dates))
    issues = get_title_issues(title_id, year)
    issue_dates = [issue['date'] for issue in issues]
    for issue_date in issue_dates:
        if not issue_date in article_dates: missing_dates.append(issue_date)
    print 'Total articles: %s' % article_count
    print 'Odd pages: %s' % len(odd_pages)
    print 'Short articles: %s' % len(short_articles)
    print 'Long articles: %s' % len(long_articles)
    print 'Duplicate dates: %s' % len(duplicate_dates)
    print 'Found articles: %s' % len(articles_filtered)
    print 'Missing articles: %s' % len(missing_dates)
    results = {'id': title_id,
               'name': title_name,
               'odd': odd_pages,
               'short': short_articles,
               'long': long_articles,
               'articles': articles_filtered,
               'duplicates': duplicate_dates,
               'missing': missing_dates,
               'issues': len(issues)
               }
    json_file = '%s/json/%s.js' % (NMA_FOLDER, os.path.basename(csv_file)[:-4])
    print json_file
    with open(json_file, 'wb') as json_data:
        json.dump(results, json_data, indent=2)
    return results

def harvest_editorials(year, titles=None):
    if not titles:
        titles = get_titles_by_year(year)
    for title in titles:
        # Remove bracketed details from name for search string
        query_str = re.search(r'([\w\s\-,\']+)?\(*', title['name']).group(1).strip()
        clean_name = clean_filename(query_str)
        filename = '%s/%s-%s.csv' % (NMA_FOLDER, title['id'], clean_name)
        if not os.path.exists(filename):
            # construct url
            url = quote_plus('http://trove.nla.gov.au/newspaper/result?q="%s" NOT (fulltext:letter OR fulltext:editor)&l-textSearchScope=headings+only|scope:headings&fromyyyy=%s&toyyyy=%s&l-title=|%s&l-category=Article|category:Article' % (query_str, year, year, title['id']), '://?=&-,\'')
            print url
            # harvest results
            harvester = TroveNewspapersHarvester()
            harvester.harvest(url, filename=filename, text=True)

def create_corpus(path):
    '''
    Create a corpus from a directory full of text files.
    '''
    articles = PlaintextCorpusReader(path, '.*\.txt')
    return articles

class ServerError(Exception):
    pass
        
if __name__ == "__main__":
    #check_csv('/Users/tim/Documents/NMA/1913/smh-editorials.csv', year=1913, exclude=[6])
    #harvest_editorials(1913)
    #check_editorials('/Users/tim/Documents/NMA/1913/editorials/titles/53-Barrier-Miner.csv', 1913)
    check_all_editorials(NMA_FOLDER, 1913)