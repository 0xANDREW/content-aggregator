import sys
import time
import datetime
from pprint import pprint
import logging

import feedparser
from bs4 import BeautifulSoup
import requests
import soupselect
import re
import dateutil.parser

from model import *

logging.getLogger('requests').setLevel(logging.WARNING)

MODULE_LOG_LEVEL = logging.DEBUG

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s %(message)s'))
ch.setLevel(MODULE_LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(MODULE_LOG_LEVEL)
logger.addHandler(ch)

class DuplicateException(Exception):
    pass

class ProcessingError(Exception):
    pass

class DateLimitException(Exception):
    pass

# Generic scraper class
class SiteScraper:
    RSS = False
    START_DATE = datetime.datetime(2014, 1, 1)

    # Base implementation always returns None
    def _next_link(self, soup):
        return None

    # Get a specified URL or the page/feed URL for the child class
    def get(self, url=None):
        if self.RSS:

            # Allow multiple feeds to be aggregated
            if type(self.URL) == list:
                return [ feedparser.parse(url)['entries'] for url in self.URL ]
            else:
                return feedparser.parse(self.URL)['entries']
        else:
            url = self.URL if url is None else url
            return BeautifulSoup(requests.get(url).text)

    # Convert a string or time struct into a datetime
    def get_date(self, date):
        if type(date) in (str, unicode):
            return dateutil.parser.parse(date)
        else:
            return datetime.datetime.fromtimestamp(time.mktime(date))

    # Base scrape method for RSS and regular sites
    def scrape(self):
        logger.info('Starting scrape for %s' % self.__class__.__name__)

        num_items = 0

        try:
            if self.RSS:
                for params in self._scrape_rss(self.get()):
                    try:
                        self.__save(params)
                        num_items += 1

                    # Abort feed scrape if duplicate found
                    except DuplicateException, e:
                        logger.warning(
                            'Found duplicate item (%s), aborting (%d new items)' % (e, num_items))
                        return

                    # Abort feed scrape if start date passed
                    except DateLimitException, e:
                        logger.warning(
                            'Date limit passed (%s), aborting (%d new items)' % (e, num_items))
                        return

                logger.info('Scrape complete for %s (%d new items)' %
                            (self.__class__.__name__, num_items))
            else:
                page = 1
                link = None

                logger.debug('%d %s' % (page, self.URL))

                # Process pages until there are no more
                while 1:
                    soup = self.get(link)

                    # If _next_link() barfs, scrape is over
                    try:
                        link = self._next_link(soup)
                    except:
                        link = None

                    for item in self._get_items(soup):
                        try:
                            params = self._process_item(item)

                        # Catch all processing errors, skip item
                        except Exception, e:
                            logger.error('Processing error, skipping item')
                            logger.exception(e)
                            continue

                        try:
                            self.__save(params)
                            num_items += 1

                        except DuplicateException, e:
                            logger.warning(
                                'Found duplicate item (%s), aborting (%d new items)' % (e, num_items))
                            break

                        except DateLimitException, e:
                            logger.warning(
                                'Date limit passed (%s), aborting (%d new items)' % (e, num_items))
                            break

                    # Commit after each page is processed
                    session.commit()

                    # When next page link is None, scrape's complete
                    if link is None:
                        logger.info('Scrape complete for %s (%d new items)' %
                                    (self.__class__.__name__, num_items))
                        break
                        
                    else:
                        page += 1
                        logger.debug('%d %s' % (page, link))

        # Log any uncaught exceptions (network errors)
        except Exception, e:
            logger.error('Uncaught error in %s (network error?)' % 
                         self.__class__.__name__)
            logger.exception(e)

        # Commit any stragglers (?)
        session.commit()

    def __save(self, params):

        if self.CLS in (Article, Publication):
            if 'date' not in params:
                logger.error('Date missing from %s' % params['url'])
                return

            if params['date'] <= self.START_DATE:
                raise DateLimitException(params['date'])

        params['time_scraped'] = datetime.datetime.now()
        params['scraper_type'] = self.__class__.__name__

        # Always convert body to unicode
        params['body'] = unicode(params['body'])

        query = self.CLS.query.filter_by(
                url=params['url'], 
                scraper_type=params['scraper_type'])

        if query.count() == 0:
            self.CLS(**params)
        else:
            raise DuplicateException(params['url'])

class WBSouthAsia(SiteScraper):
    URL = 'http://www.worldbank.org/en/region/sar/whats-new'
    URL_BASE = 'http://www.worldbank.org'
    CLS = Article

    def _next_link(self, soup):
        rv = None

        for a in soupselect.select(soup, 'div.f05v3-pagination li a'):
            if a.text.startswith('NEXT'):
                rv = self.URL_BASE + a['href']

        return rv

    def _get_items(self, soup):
        return soupselect.select(soup, 'div.n07v3-generic-list-comp')

    def _process_item(self, article):
        title = article.find('h6').text.strip()
        url = article.find('h6').find('a')['href']
        desc = article.find('div', class_='description')
        body = ''

        # Remove JavaScript from body
        if desc:
            toggle = desc.find('span', id='summary_1')

            if toggle:
                toggle.decompose()

            detail = desc.find('span', id='detail_1')

            if detail:
                detail.a.decompose()

        date = re.search('Date: (.+)', article.text).groups()[0]

        return {
            'title': title,
            'url': url,
            'body': desc if desc else body,
            'date': self.get_date(date)
        }

class WBEastAsia(WBSouthAsia):
    URL = 'http://www.worldbank.org/en/region/eap/whats-new'

class AsianDevelopmentBank(SiteScraper):
    URL = 'http://feeds.feedburner.com/adb_news'
    RSS = True
    CLS = Article

    def _scrape_rss(self, items):
        rv = []

        for article in items:
            rv.append({
                'title': article['title'],
                'url': article['feedburner_origlink'],
                'body': article['summary'],
                'date': self.get_date(article['published'])
            })

        return rv

class ASEAN(SiteScraper):
    URL = 'http://www.asean.org/news'
    URL_BASE = 'http://www.asean.org'
    CLS = Article

    def _next_link(self, soup):
        return self.URL_BASE + soupselect.select(
            soup, 'div.pagination-bg a.next')[0]['href']

    def _get_items(self, soup):
        return soupselect.select(soup, 'div.teaser-item')

    def _process_item(self, item):
        title = item.find('h1').text
        url = self.URL_BASE + item.find('h1').find('a')['href']
        rough_date = item.find('p').text
        body = item.find('div', class_='floatbox')

        m = re.search('(\d{2} \w+ \d{4})', rough_date)
        date = self.get_date(m.groups()[0])

        return {
            'title': title,
            'url': url,
            'body': body,
            'date': date
        }

class UNESCAP(SiteScraper):
    URL = 'http://www.unescap.org/media-centre/feature-stories'
    URL_BASE = 'http://www.unescap.org'
    CLS = Article

    def _get_items(self, soup):
        return soupselect.select(soup, 'div.view-mode-feature_story .group-right')

    def _process_item(self, item):
        title = item.find('h2').find('a').text
        url = self.URL_BASE + item.find('h2').find('a')['href']
        date = self.get_date(soupselect.select(
            item, '.date-display-single')[0].text)
        body = item.find('div', class_='field-name-body')

        return {
            'title': title,
            'url': url,
            'body': body,
            'date': date
        }

class CACAARI(SiteScraper):
    URL = 'http://www.cacaari.org/news/rss'
    RSS = True
    CLS = Article

    def _scrape_rss(self, items):
        rv = []

        for item in items:
            rv.append({
                'title': item['title'],
                'url': item['guid'],
                'date': self.get_date(item['published_parsed']),
                'body': item['summary']
            })

        return rv

class UCentralAsiaNewsScraper(SiteScraper):
    URL = 'http://www.ucentralasia.org/news.asp'
    URL_BASE = 'http://www.ucentralasia.org'
    CLS = Article

    def _get_items(self, soup):
        rv = []
        brs = soup.select('#centre > br')

        # Article listing is a mess of <p> tags, but luckily separated by <br>
        for br in brs:
            rv.append([
                br.previousSibling,
                br.previousSibling.previousSibling
            ])

        return rv

    def _process_item(self, item):
        if item[0].name != 'p' and item[1] != 'p':
            raise ProcessingError()

        date_text = item[1].select('span')[0].text
        m = re.search('(\d+ \w+ \d+)', date_text)
    
        return {
            'title': item[1].select('a')[0].text,
            'url': '%s/%s' % (self.URL_BASE, item[1].select('a')[0]['href']),
            'body': item[0].text,
            'date': self.get_date(m.group(1))
        }        

# RSS doesn't actually include parseable event dates
class APARRIEventScraper(SiteScraper):
    URL = 'http://www.apaari.org/events/feed/'
    RSS = True
    CLS = Event

    def _scrape_rss(self, items):
        rv = []

        for item in items:
            rv.append({
                'title': item['title'],
                'url': item['link'],
                'date': self.get_date(item['published_parsed']),
                'body': item['summary']
            })

        return rv

class UNESCAPEventScraper(SiteScraper):
    URL = 'http://www.unescap.org/events/upcoming'
    URL_BASE = 'http://www.unescap.org'
    CLS = Event

    def _next_link(self, soup):
        return self.URL_BASE + soupselect.select(
            soup, 'li.pager-next a')[0]['href']

    def _get_items(self, soup):
        return soupselect.select(soup, 'div.item-list li.views-row')

    def _process_item(self, li):
        title = li.find('h2').find('a').text
        url = self.URL_BASE + li.find('h2').find('a')['href']
        start_time = None
        end_time = None

        container = soupselect.select(
            li, 'div.field-name-field-event-dates')[0]

        single = soupselect.select(container, 'span.date-display-single')

        if len(single) > 0:
            start_time = self.get_date(single[0].text)
        else:
            start_time = self.get_date(soupselect.select(
                container, 'span.date-display-start')[0].text)
            end_time = self.get_date(soupselect.select(
                container, 'span.date-display-end')[0].text)

        event_type = unicode(soupselect.select(
            li, 'div.field-name-field-event-type')[0])
        event_loc = ''

        try:
            event_loc = unicode(
                soupselect.select(li, 'div.field-name-venue')[0])
        except:
            pass

        body = event_type + event_loc

        return {
            'title': title,
            'url': url,
            'start_time': start_time,
            'end_time': end_time,
            'body': body
        }

class WBSouthAsiaPubScraper(WBSouthAsia):
    URL = 'http://www.worldbank.org/en/region/sar/research/all'
    CLS = Publication
    START_DATE = datetime.datetime(2010, 1, 1)

class WBEastAsiaPubScraper(WBSouthAsiaPubScraper):
    URL = 'http://www.worldbank.org/en/region/eap/research/all'

class ADBPubScraper(SiteScraper):
    URL = 'http://feeds.feedburner.com/adb_publications'
    RSS = True
    CLS = Publication
    START_DATE = datetime.datetime(2010, 1, 1)

    def _scrape_rss(self, items):
        rv = []

        for item in items:
            rv.append({
                'title': item['title'],
                'url': item['link'],
                'body': item['description'],
                'date': self.get_date(item['published_parsed'])
            })

        return rv

class UNESCAPPubScraper(SiteScraper):
    URL = 'http://www.unescap.org/publications'
    URL_BASE = 'http://www.unescap.org'
    CLS = Publication
    START_DATE = datetime.datetime(2010, 1, 1)

    def _next_link(self, soup):
        return self.URL_BASE + soupselect.select(
            soup, '.pager-next a')[0]['href']

    def _get_items(self, soup):
        return soupselect.select(soup, '.view-content .views-row')

    def _process_item(self, item):
        link = item.find('a')
        title = link.text
        url = self.URL_BASE + link['href']
        body = soupselect.select(item, '.field-name-body p')[0].text
        date = self.get_date(
            soupselect.select(item, '.date-display-single')[0].text)

        return {
            'title': title,
            'url': url,
            'date': date,
            'body': body
        }
