'''
Created on 12/04/2011

@author: tim
'''
from __future__ import with_statement
import string
import re
try:
    import json
except ImportError:
    import simplejson as json

import scrape

def main():
    news = scrape.TroveNewspapersClient(titles=True)
    #summary_all(news)
    #summary_by_state(news)
    summary_by_title(news)

def summary_all(news):
    #Total number of articles by year
    totals = {}
    for year in range(1803, 1955):
        args = {}
        args['fromyyyy'] = str(year)
        args['toyyyy'] = str(year)
        news.reset()
        news.tries = 10
        news.search(**args)
        total = int(string.replace(news.total_results, ',', ''))
        totals[year] = total
        print '%s: %s' % (year, total)
    total_list = [[year, total] for year, total in totals.items()]
    with open('graph/data/summary-totals.js', 'wb') as jsfile:
        jsfile.write('var totals = %s;' % json.dumps(total_list))
    print 'Completed!'
    
def summary_by_state(news):
    #Total number of articles by state
    totals = {}
    for state in scrape.STATES:
        totals[state] = {}
        for year in range(1803, 1955):
            args = {}
            args['fromyyyy'] = str(year)
            args['toyyyy'] = str(year)
            args['state'] = state
            news.reset()
            news.tries = 10
            news.search(**args)
            total = int(string.replace(news.total_results, ',', ''))
            totals[state][year] = total
            print '%s %s: %s' % (state, year, total)
    with open('graph/data/summary-totals-bystate.js', 'wb') as jsfile:
        for state, values in totals.items():
            total_list = [[year, total] for year, total in values.items()]
            jsfile.write('var %s_totals = %s;\n' % (state, json.dumps(total_list)))
    print 'Completed!'
    
def summary_by_title(news):
    #Total number of articles by state/title
    for state in scrape.STATES:
    #for state in ['act', 'vic']:
        labels = []
        series = []
        totals = {}
        titles = news.titles_by_state[state]
        for title in titles:
            name = re.sub(' \(.*\)', '', title['name'])
            totals[title['id']] = {}
            start = int(title['start_year'])
            end = int(title['end_year'])
            for year in range(start, end+1):
                args = {}
                args['fromyyyy'] = str(year)
                args['toyyyy'] = str(year)
                args['l_title'] = '|%s' % title['id']
                news.reset()
                news.tries = 10
                news.search(**args)
                print news.query
                total = int(string.replace(news.total_results, ',', ''))
                totals[title['id']][year] = total
                print '%s %s: %s' % (name, year, total)
            if totals[title['id']]:
                series.append([title['id'], name])
        with open('graph/data/summary-totals-%s.js' % state, 'wb') as jsfile:
            data = {}
            results = {}
            for title, values in totals.items():
                total_list = [[year, total] for year, total in values.items()]
                data[title] = total_list
            results['data'] = data
            results['titles'] = series
            jsfile.write('var graph_data = %s;\n' % json.dumps(results))
    print 'Completed!'

if __name__ == "__main__":
    main()