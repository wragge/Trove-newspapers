'''
retrieve.py
Created on 04/02/2010
@author: tim

Provides a class for interacting with the Trove newspapers database.

USAGE:

Initialise client:
client = retrieve.TroveNewspapersClient()

Do a basic search:
client.search(q=clement+wragge&)

Find out the number of results:
total_results = client.total_results

Retrieve search results:
results = client.results

Retrieve details of an individual article:
client.get_article('12324423')
results = client.results

Get random articles from 1945:
client.get_random(year=1945)
results = client.results

Copyright (C) 2011 Tim Sherratt
This file is part of the TroveNewspapers package.

The TroveNewspapers package is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The TroveNewspapers package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with the TroveNewspapers package. If not, see <http://www.gnu.org/licenses/>.
'''
from BeautifulSoup import BeautifulSoup
import re
import random
from urllib2 import Request, urlopen, URLError, HTTPError
import urllib2
from time import sleep
from urllib import quote_plus
from string import replace
import time

from utilities import open_titles

SEARCH_PATH = "http://trove.nla.gov.au/newspaper/result?"
IMAGE_PATH = "http://trove.nla.gov.au/ndp/imageservice/nla.news-page"
STATES = ['nsw', 'act', 'nt', 'qld', 'sa', 'tas', 'vic', 'wa', 'national']
SORT_OPTIONS = ['', 'dateAsc', 'dateDesc']

class TroveNewspapersClient:
    
    def __init__(self, titles=True, user=None, password=None):
        if titles:
            self.titles_by_state = open_titles('state')
            self.titles_by_id = open_titles('id')
        else:
            self.titles_by_state = None
            self.titles_by_id = None
        self.query = ''
        self.response = None
        self.results = []
        self.total_results = 0
        self.tries = 1
        self.user = user
        self.password = password
        
    def reset(self):
        self.query = ''
        self.response = None
        self.results = []
        self.total_results = 0
        self.tries = 1
        
    def search(self, **kwargs):
        '''
        Retrieve results using supplied parameters.
        Query parameters (all parameters are optional):            
            q
            exactPhrase
            anyWords
            notWords
            l-textSearchScope
                *ignore*|*ignore* (anywhere)
                headings+only|scope:headings
                headings,+author,+1st+4+lines|scope:headingsAuthorAbstract
                captions+only|scope:captions
            fromdd
            frommm
            fromyyyy
            todd
            tomm
            toyyyy
            l-title (multiple)
                |[title id]
            l-category (multiple)
                Advertising|category:Advertising
                Article|category:Article
                Detailed+lists,+results,+guides|category:Detailed+lists,+results,+guides
                Family+Notices|category:Family+Notices
                Literature|category:Literature
            l-word
                *ignore*|*ignore* (all)
                <+100+words|sizecategory:0
                100-1000+words|sizecategory:1
                >+1000+words|sizecategory:3
            l-illustrated
                Illustrated|anyillustrations:y
            sortby
                (default: relevance)
                dateAsc
                dateDesc
            s (start number)
                (a multiple of 20)
        '''
        if 'url' in kwargs:
            self.query = kwargs['url']
        else:
            self.make_query(**kwargs)
        #print self.query
        try:
            self.try_url()
        except Exception:
            raise
        else:    
            try:
                self.extract_results()
            except Exception:
                raise
        
    def get_random_articles(self, year=None, 
                                state=None, 
                                titles=None, 
                                kw_all=None, 
                                kw_any=None, 
                                kw_exact=None, 
                                kw_exclude=None, 
                                filters=None, 
                                mask=False):
        '''
        Retrieve a random set of results.
        The 'randomness' can be adjusted and the content filtered by supplying parameters.
        The filters -- 'title' and 'month' -- increase the pool of possible results by selecting random titles and/or months.
        
        Examples:
        get_random_articles(year="1920", q="cricket") -- will return random results from 1920 containing the keyword 'cricket'.
        get_random_articles(titles=["112"]) -- will return random results from the Australian Women's Weekly
        
        Sets self.results to a list of dictionaries, each containing:
        
            'title': article title,
            'id': article id number (can be used in get_article to retrieve further details)
            'newspaper': newspaper title,
            'newspaper_details': newspaper life dates and location
            'issue_date': issue date in form 'Wednesday 2 July 1958'
            'page': page number
            'type': type of article
            'length': number of words 
            'summary': first few lines of article
            'url': url of article            
        '''
        if kw_all or kw_any or kw_exact or kw_exclude:
            parameters = dict(self.make_random_query(year=year, 
                                                     state=state, 
                                                     titles=titles, 
                                                     filters=filters), 
                                                     **self.make_keyword_query(kw_all, 
                                                                               kw_any, 
                                                                               kw_exact, 
                                                                               kw_exclude))
        else:
            parameters = self.make_random_query(year=year, state=state, 
                                                titles=titles, filters=filters)
        parameters['sortby'] = random.choice(SORT_OPTIONS)
        parameters['l-category'] = 'Article|category:Article'
        self.search(**parameters)
        if mask: 
            self.mask_dates(year)
    
    def get_article(self, article_id):
        '''
        Get the details of a specific article using its ID.
        Example: get_article('13855894').
        Returns a dictionary:
            'title': article title,
            'id': article id number (can be used in get_article to retrieve further details)
            'url': url of article
            'newspaper': newspaper title,
            'newspaper_details': newspaper life dates and location
            'issue_date': issue date in form 'Wednesday 2 July 1958'
            'page': page number
            'page_url': url of whole page in which this article was published
            'thumb_url': url of page thumbnail
            'tile_url': url of first image tile of page
            'corrections': number of OCR corrections made
            'text': text of article            
        '''
        self.query = 'http://nla.gov.au/nla.news-article%s' % article_id
        try:
            self.try_url()
        except Exception:
            raise
        else:
            self.results = self.extract_article_details()
            
    def make_query(self, **kwargs):
        '''
        Create search query from supplied parameters.
        '''
        url = SEARCH_PATH
        kwargs = self.process_args(**kwargs)
        url += '&'.join(['%s=%s' % (k.replace('_','-'), quote_plus(v,'*+|&=')) 
                                    for (k, v) in kwargs.items()])
        self.query = url

    def process_args(self, **kwargs):
        '''
        Converts lists into key=value1&key=value2 strings for 
        inclusion in search query.
        '''
        for (key, value) in kwargs.items():
            if type(value).__name__ == 'list':
                kwargs[key] = (('&%s=' % key.replace('_','-'))
                                .join([v for v in value]))
            if key == 'state' and value in STATES:
                titles = self.list_titles(value)
                kwargs['l-title'] = ('&l-title=').join(['|%s' % t for t in titles])
                del kwargs['state']
        return kwargs
    
    def list_titles(self, state):
        titles = self.titles_by_state[state]
        return [title['id'] for title in titles]
    
    def make_keyword_query(self, kw_all, kw_any, kw_exact, kw_exclude):
        '''
        Converts keyword search parameters into expected format.
        '''
        parameters = {}
        if kw_all:
            parameters['q'] = kw_all
        if kw_exact:
            parameters['exactPhrase'] = kw_exact
        if kw_any:
            parameters['anyWords'] = kw_any
        if kw_exclude:
            parameters['notWords'] = kw_exclude
        return parameters

    def generate_random_selection(self, year=None, state=None, 
                                  titles=None, filters=None):
        '''
        Generate a random combination of month, year and title within the 
        limits of the current digitised holdings.
        You can optionally supply a year or a list of titles.
        Using the 'title' and 'month' filter options increases the chance 
        that multiple calls will retrieve different results. 
        The 'title' filter also ensures that a greater variety of titles are exposed.
        '''
        if titles:
            try:
                title = self.titles_by_id[int(random.choice(titles))]
            except KeyError:
                title = self.titles_by_id[random.choice(titles)]
            title_id = title['id']
        elif state and state in STATES:
            if not year:
                title = random.choice(self.titles_by_state[state])
            else:
                year = int(year)
                titles = [ t for t in self.titles_by_state[state] 
                          if year >= int(t['start_year']) and 
                            year <= int(t['end_year'])]
                title = random.choice(titles)
            title_id = title['id']
        else:
            title = None
        if filters is None:
            filters = []
        #If no year, choose a year in which issues for selected title are available
        if not year:
            if title or 'title' in filters:
                if not title:
                    title = random.choice(self.titles_by_id.values())
                    title_id = title['id']
                year = random.randrange(int(title['start_year']), 
                                        int(title['end_year'])+1)
            else:
                year = random.randrange(1803, 1982)
                title_id = ''
        else:
            year = int(year)
            # If year is given, find newspapers that have issues in that year
            if title or 'title' in filters:
                if not title:
                    titles = [t for t in self.titles_by_id.values() 
                              if year >= int(t['start_year']) 
                                and year <= int(t['end_year']) ]
                    title = random.choice(titles)
                    title_id = title['id']
            else:
                title_id = ''
        # Set month
        if 'month' in filters:
            if title and year == int(title['start_year']):
                start_month = int(title['start_month'])
            else:
                start_month = 1
            if title and year == int(title['end_year']):
                end_month = int(title['end_month'])
            else:
                end_month = 12
            month = random.randrange(start_month, end_month+1)
        else:
            month = ''
        return {'title': title_id, 'year': str(year), 'month': str(month)}
    
    def make_random_query(self, **kwargs):
        '''
        Build up search query from parameters.
        '''
        parameters = {}
        random_q = self.generate_random_selection(year=kwargs['year'], 
                                                state=kwargs['state'], 
                                                titles=kwargs['titles'], 
                                                filters=kwargs['filters'])        
        if random_q['year']:
            parameters['fromyyyy'] = random_q['year']
            parameters['toyyyy'] = random_q['year'] 
        if random_q['month']:
            parameters['frommm'] = random_q['month'].rjust(2, '0')
            parameters['tomm'] = random_q['month'].rjust(2, '0')
        if random_q['title']:
            parameters['l_title'] = '|' + random_q['title']
        return parameters   

    def extract_results(self):
        '''
        Extracts individual results from results page and 
        sends them off for processing.
        '''
        page = BeautifulSoup(self.response)
        self.total_results = (page.find('div', attrs={'id': 'newspapers'})
                                        .find('div', 'hdrresult')
                                        .p.strong.string.strip().replace(',',''))
        self.results = [self.extract_details(result) 
                        for result in page.find('div', {'id': 'newspapers'})
                                                .findAll('dl')]
    
    def extract_details(self, result):
        '''
        Extracts details of each individual result.
        '''
        article = {}
        if result.dt.a is not None:
            if result.dt.a.string.strip() == '[coming soon]':
                title = result.dt.contents[0].string.strip()
                url = ''
                article_id = ''
            else:
                title = result.dt.a.string.strip()
                path = result.dt.a['href']
                article_id = re.search(r'\/(\d+)\?', path).group(1)
                url = 'http://nla.gov.au/nla.news-article%s' % article_id
        else:
            title = result.dt.span.string.strip()
            url = ''
            article_id = ''
        article['title'] = title
        article['id'] = article_id
        article['url'] = url
        publication_fields = result.find('dd', 'sourcedate')
        if '(' in publication_fields.i.string:
            newspaper_title, newspaper_details = (re.search(r'(.*?) \((.*?)\)', 
                                                           publication_fields
                                                           .i.string.strip())
                                                           .groups())
        else:
            newspaper_title = publication_fields.i.string.strip()
            newspaper_details = ''
        article['newspaper_title'] = newspaper_title
        article['newspaper_details'] = newspaper_details
        article['issue_date'] = publication_fields.b.string.strip()
        article['issue_year'], article['issue_month'], article['issue_day'] = extract_date(article['issue_date'])
        article['page'], article['type'] = (re.search(r'(\d+) (.*)', 
                                                      publication_fields.contents[3]
                                                      .string.strip()).groups())
        article['length'] = result.find('dd', 'snippet').span.string.strip()
        article['summary'] = ''.join([e.string.strip() for e in 
                                      result.find('dd', 'snippet').contents[:-1]])
        return article
        
    def extract_article_details(self):
        '''
        Extract the details from an individual article page.
        '''
        article = {}
        page = BeautifulSoup(self.response)
        article['id'] = self.query[34:]
        article['url'] = self.query
        article['title'] = (page.find(attrs = {'name': 'newsarticle_headline'})['content']
                                    .encode('utf-8'))
        if '(' in page.find('div','title').strong.string:
            newspaper, details = (re.search(r'(.*?) \((.*?)\)', page.find('div','title')
                                .strong.string.strip()).groups())
        else:
            newspaper = page.find('div','title').strong.string.strip()
            details = ''
        article['newspaper_title'] = newspaper
        article['newspaper_details'] = details
        article['newspaper_id'] = (re.search(r'\/(\d+)$', 
                                            page.find('span', 'about')
                                            .a['href']).group(1))
        article['issue_date'] = page.find('div', 'issue').strong.string.strip()
        article['issue_year'], article['issue_month'], article['issue_day'] = extract_date(article['issue_date'])
        article['page'] = (page.find('select', attrs = {'name': 'id'})
                            .find('option', attrs = {'selected': 'selected'}).string.strip())
        page_id = re.search(r'var pageId = \'(\d+)\'', self.response).group(1)
        article['page_url'] = 'http://nla.gov.au/nla.news-page' + page_id
        article['tile_url'] = '%s%s/tile0-0-0' % (IMAGE_PATH, page_id)
        article['thumb_url'] = '%s%s/thumb' % (IMAGE_PATH, page_id)
        if page.find('p', 'numCorrections').contents[0].strip() == 'No corrections yet':
            article['corrections'] = 0
        else:
            article['corrections'] = int(re.match('^(\d+)', 
                                                  page.find('p', 'numCorrections')
                                                  .contents[0].strip()).group(1))
        paras = page.find('div', 'ocr-text').findAll('p')
        ftext = ''
        text = ''
        for para in paras:
            ftext += replace('<p>%s</p>' % ('').join([line.string 
                                                      for line in para.findAll('span') 
                                                      if line.string]).strip(),'  ',' ')
            text += ('').join([line.string for line in 
                               para.findAll('span') if line.string]).strip()
        text = replace(text, '&nbsp;', ' ')
        text = replace(text, '  ', ' ')
        article['ftext'] = ftext.encode('utf-8')
        article['text'] = text.encode('utf-8')
        return article
    
    def mask_dates(self, year):
        '''
        Hide dates in headlines and summaries.
        '''
        pattern = re.compile(r'\b%s\b' % year)
        for result in self.results:
            result['title'] = pattern.sub(' **** ', result['title'])
            result['summary'] = pattern.sub(' **** ', result['summary'])                 

    def try_url(self):
        '''
        Set up a loop to retry downloads in the case of server (5xx) errors.
        '''
        success = False
        try_num = 1
        while success is False and try_num <= self.tries:
            if try_num > 1:
                time.sleep(10)
            try:
                response = self.get_url()
            except Exception:
                raise
            else:
                if response is not None:
                    success = True
                else:
                    if try_num == self.tries:
                        raise ServerError('Nothing was returned')
                    else:
                        try_num += 1
        self.response = response.read()

    def get_url(self):
        '''
        Retrieve page.
        '''
        if self.user and self.password:
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, 'trove.nla.gov.au', self.user, self.password)
            authhandler = urllib2.HTTPBasicAuthHandler(passman)
            opener = urllib2.build_opener(authhandler)
            urllib2.install_opener(opener)
        user_agent = 'Mozilla/5.0 (X11; Linux i686; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'
        headers = { 'User-Agent' : user_agent }
        req = Request(self.query, None, headers)
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

def extract_date(date_string):
    '''
    Extracts year, month and day integers from issue date string.
    '''
    cleaned_date = re.match('^(\w+ \d{1,2} \w+ \d{4})', date_string).group(1)
    date_tuple = time.strptime(cleaned_date, '%A %d %B %Y')
    year = date_tuple[0]
    month = date_tuple[1]
    day = date_tuple[2]
    return (year, month, day)

class ServerError(Exception):
    pass

if __name__ == "__main__":
    #Examples
    np = TroveNewspapersClient(user='wragge', password='brillig')
    #np.search(exactPhrase="inclement wragge")
    #np.search(url="http://trove.nla.gov.au/newspaper/result?q=&exactPhrase=inclement+wragge")
    np.search(url="https://trove.nla.gov.au/newspaper/result?l-usertag=test2&q=")
    #np.search(state="vic")
    #np.get_random_articles(year="1880", kw_all="kelly", kw_any="ireland irish")
    #np.get_random_articles(year="1880", filters=['title', 'month'])
    #np.get_random_articles(year="1880", titles=['35'])
    #np.get_article('61658218')
    print np.query
    print np.total_results
    print np.results

        