#!/usr/bin/env python
import json
import re
import os
import shutil
import urllib
from urllib2 import Request, urlopen, URLError, HTTPError

from utilities import get_url
from keys import YAHOO_ID

TITLES_URL = 'http://trove.nla.gov.au/ndp/del/titleList'
TITLE_HOLDINGS_URL = 'http://trove.nla.gov.au/ndp/del/yearsAndMonthsForTitle/'
YAHOO_URL = 'http://wherein.yahooapis.com/v1/document'

def get_titles(locate=False):
    '''
    Retrieves a list of current newspaper titles from Trove.
    Retrieves current holdings details about each title.
    Saves details of newspapers with holdings to a list.
    Returns a list of dictionaries with the following fields:
    name, id, state, start_year, start_month, end_year, end_month.
    '''
    title_list = json.load(get_url(TITLES_URL))
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
        if locate and place is None and state is not 'national':
            locate_title(name)       
        url = '%s%s' % (TITLE_HOLDINGS_URL, title['id'])
        holdings = json.load(get_url(url))
        #Only save those who have holdings online
        if len(holdings) > 0:
            titles.append({'name': name,
                               'id': title['id'],
                               'state': state,
                               'place': place,
                               'start_year': holdings[0]['y'],
                               'start_month': holdings[0]['m'],
                               'end_year': holdings[-1]['y'],
                               'end_month': holdings[-1]['m'],
                               })
    return titles

def sort_directories_by_state(path):
    titles = { title['id']: title for title in get_titles() }
    dirs = [ dir for dir in os.listdir(path) if os.path.isdir(os.path.join(path, dir)) and dir != 'states' ]
    state_dir = os.path.join(path, 'states')
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)
    for dir in dirs:
        id = re.match(r'(\d+)\-', dir).group(1)
        state = titles[id]['state']
        this_dir = os.path.join(state_dir, state.lower())
        if not os.path.exists(this_dir):
            os.makedirs(this_dir)
        shutil.copytree(os.path.join(path, dir), os.path.join(this_dir, dir))

def show_metro():
    cities = ['Melbourne', 'Sydney', 'Brisbane', 'Perth', 'Adelaide', 'Hobart']
    titles = get_titles()
    metro = {}
    for title in titles:
        if title['place'] in cities:
            metro[title['id']] = title
        elif look_for_city(title['name'], cities):
            metro[title['id']] = title
    for paper in metro.itervalues():
        print paper['name']
         
def look_for_city(name, cities):
    found = False
    for city in cities:
        if city in name:
            found = True
            break
    return found
    
def locate_title(title):
    '''
    Attempt to extract placenames from newspaper titles.
    '''
    values = {'appid': YAHOO_ID, 'documentType': 'text/plain', 'documentContent': unicode(title).encode('utf-8') + ' Australia', 'outputType': 'json'}
    data = urllib.urlencode(values)
    req = Request(YAHOO_URL, data)
    response = urlopen(req)
    place_data = json.load(response)
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

def get_titles_by_year(year):
    '''
    Create a list of newspaper titles with issues published in the specified year.
    '''
    all_titles = get_titles()
    titles = [title for title in all_titles if (int(title['start_year']) <= year and int(title['end_year']) >= year)]
    return titles

    