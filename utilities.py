'''
Created on 19/11/2010

@author: tim
'''
from __future__ import with_statement
import re
try:
    import json
except ImportError:
    import simplejson as json 
import pickle
import urllib
from urllib2 import Request, urlopen, URLError, HTTPError
import time
import os
import calendar
import datetime
import string

YAHOO_ID = 'JAp9z33V34HzR4rvRaHUNsRuEadGdaoQlRWYwsObAM1YquTZ.m92jjrhx.X0mOro67op'
YAHOO_URL = 'http://wherein.yahooapis.com/v1/document'

def get_titles(locate=False):
    '''
    Retrieves a list of current newspaper titles from Trove.
    Retrieves current holdings details about each title.
    Saves details of newspapers with holdings to a list.
    Returns a list of dictionaries with the following fields:
    name, id, state, start_year, start_month, end_year, end_month.
    '''
    url = "http://trove.nla.gov.au/ndp/del/titleList"
    title_list = json.load(get_url(url))
    titles = []
    for title in title_list:
        name = title['name']
        print unicode(name).encode('utf-8')
        try:
            place, state = re.search(r'\(([a-zA-Z \.]+, )*?(National|ACT|NSW|NT|Qld|QLD|SA|Tas|TAS|Vic|VIC|WA)\.*?', 
                              name).groups()
        except AttributeError:
            place = None
            state = 'national'
        print 'Place: %s' % place
        print 'State: %s' % state
        if locate and place is None and state is not 'national':
            values = {'appid': YAHOO_ID, 'documentType': 'text/plain', 'documentContent': unicode(name).encode('utf-8') + ' Australia', 'outputType': 'json'}
            data = urllib.urlencode(values)
            req = Request(YAHOO_URL, data)
            response = urlopen(req)
            place_data = json.loads(response.read())
            print place_data
            if isinstance(place_data['document']['localScopes'], list):
                for scope in place_data['document']['localScopes']:
                    print scope['localScope']['name']
            else:
                print place_data['document']['localScopes']['localScope']['name']
            try:
                print place_data['document']['placeDetails']['place']['name']
            except KeyError:
                print "No place"        
        url = 'http://trove.nla.gov.au/ndp/del/yearsAndMonthsForTitle/%s' % title['id']
        holdings = json.loads(get_url(url).read())
        #Only save those who have holdings online
        if len(holdings) > 0:
            titles.append({'name': name,
                               'id': title['id'],
                               'state': state,
                               'start_year': holdings[0]['y'],
                               'start_month': holdings[0]['m'],
                               'end_year': holdings[-1]['y'],
                               'end_month': holdings[-1]['m'],
                               })
    return titles            
            
def get_url(url, try_num=0):
    '''
    Retrieve page.
    '''
    if try_num < 10:
        user_agent = 'Mozilla/5.0 (X11; Linux i686; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'
        headers = { 'User-Agent' : user_agent }
        req = Request(url, None, headers)
        try:
            response = urlopen(req)
        except HTTPError, error:
            if error.code >= 500:
                time.sleep(10)
                get_url(url, try_num =+ 1)
            else:
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', error.code
        except URLError, error:
            print 'We failed to reach a server.'
            print 'Reason: ', error.reason
        else:
            return response
    else:
        raise HTTPError

def save_titles(path=None):
    '''
    Pickles newspaper titles as dictionaries indexed by id and state.
    '''
    if not path:
        path = os.path.join(os.path.dirname(__file__), 'data/')
    titles = get_titles()
    titles_by_id = dict((title['id'], title) for title in titles)
    titles_by_state = {}
    for title in titles:
        try:
            state_titles = titles_by_state[title['state']]
            state_titles.append(title)
            titles_by_state[title['state']] = state_titles
        except KeyError:
            titles_by_state[title['state']] = [title,]
    with open('%stitles_by_id.pck' % path, 'wb') as f:
        pickle.dump(titles_by_id, f)
    with open('%stitles_by_state.pck' % path, 'wb') as f:
        pickle.dump(titles_by_state, f)

def open_titles(bykey, path=None):
    '''
    Opens pickled files and returns their contents.
    '''
    if not path:
        path = os.path.join(os.path.dirname(__file__), 'data/')
    pck_file = '%stitles_by_%s.pck' % (path, bykey)
    try:
        with open(pck_file, 'rb') as f:
            return pickle.load(f)
    except IOError:
        print 'Error opening file (are you sure it exists?)'
        print 'Use save_titles() to generate the data files.'
    except Exception:
        print 'Unknown error'

def parse_date(date):
    '''
    Parses dates from Trove of the form Friday 27 October 1911.
    '''
    months = dict((v,k) for k,v in enumerate(calendar.month_name))
    day, month, year = re.findall('\w+ (\d{1,2}) (\w+) (\d{4})', date)[0]
    month_num = months[month]
    return datetime.date(int(year), month_num, int(day))
    
def format_date(date):
    '''
    Format a nice date string. (Bypassing strftime's problems with years < 1900)
    '''
    date_tuple = date.timetuple()
    return '%s %s %s %s' % (calendar.day_name[date_tuple[6]], date_tuple[2], calendar.month_name[date_tuple[1]], date_tuple[0])

def convert_iso_to_datetime(isodate):
    '''
    Take an ISO date string YYYY-MM-DD and return a datetime.date object.
    
    >>> convert_iso_to_datetime('1925-01-01')
    datetime.date(1925, 1, 1)
    '''
    year, month, day = (int(num) for num in isodate.split('-'))
    date = datetime.date(year, month, day)
    return date

def find_duplicates(list):
    '''
    Check a list for duplicate values.
    Returns a list of the duplicates.
    '''
    seen = set()
    duplicates = []
    for item in list:
        if item in seen:
            duplicates.append(item)
        seen.add(item)
    return duplicates

def clean_filename(filename):
    '''
    Removes funny characters from strings so they can be used as filenames.
    '''
    valid_chars = '-_()%s%s' % (string.ascii_letters, string.digits)
    filename = filename.replace(' ', '-')
    filename = ''.join(c for c in filename if c in valid_chars)
    return filenimpoame
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()