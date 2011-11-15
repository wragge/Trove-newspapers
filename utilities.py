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
from urllib2 import Request, urlopen, URLError, HTTPError
import time
import os

def get_titles():
    '''
    Retrieves a list of current newspaper titles from Trove.
    Retrieves current holdings details about each title.
    Saves details of newspapers with holdings to a list.
    Returns a list of dictionaries with the following fields:
    name, id, state, start_year, start_month, end_year, end_month.
    '''
    url = "http://trove.nla.gov.au/ndp/del/titleList"
    title_list = json.loads(get_url(url).read())
    titles = []
    for title in title_list:
        name = title['name']
        print name
        try:
            state = re.search(r'\(([a-zA-Z ]+, )*?(National|ACT|NSW|NT|Qld|QLD|SA|Tas|TAS|Vic|VIC|WA)\.*?', 
                              name).group(2).lower()
        except AttributeError:
            state = 'national'
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
                get_url(url, try_num=try_num+1)
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

if __name__ == "__main__":
    #create_date_ranges()
    #create_titles_pickle()
    #save_titles(format='pickle', bykey='id')
    #save_titles(format='pickle', bykey='state')
    save_titles()