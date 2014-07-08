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

setup_all()
create_all()

class DuplicateException(Exception):
    pass

# Generic scraper class
class SiteScraper:
    RSS = False

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
        print 'Starting scrape for %s' % self.__class__.__name__

        try:
            if self.RSS:
                self._scrape_rss(self.get())
                print 'Scrape complete for %s' % self.__class__.__name__
            else:
                page = 1
                link = None

                print page, self.URL

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
                            self._process_item(item)

                        # Catch all processing errors, skip item
                        except Exception, e:
                            logging.exception(e)
                            print 'Processing error, skipping item'

                    # Commit after each page is processed
                    session.commit()

                    # When next page link is None, scrape's complete
                    if link is None:
                        print 'Scrape complete for %s' % self.__class__.__name__
                        break
                        
                    else:
                        page += 1
                        print page, link

        # Abort when dupe found
        # TODO: scan in reverse order?
        except DuplicateException, e:
            print 'Found duplicate item, aborting', e

        # Log any uncaught exceptions
        except Exception, e:
            print 'Uncaught error in %s' % self.__class__.__name__
            logging.exception(e)

        # Commit any stragglers (?)
        session.commit()

    # Save an article
    def save(self, article):
        if len(Article.query.filter_by(url=article['url']).all()) == 0:
            article['time_scraped'] = datetime.datetime.now()
            article['scraper_type'] = self.__class__.__name__

            Article(**article)
        # else:
        #     raise DuplicateException(event)

    # Save an event
    def save_event(self, event):
        if len(Event.query.filter_by(url=event['url']).all()) == 0:
            event['time_scraped'] = datetime.datetime.now()
            event['scraper_type'] = self.__class__.__name__

            Event(**event)
        # else:
        #     raise DuplicateException(event)

    # Save a publication
    def save_pub(self, pub):
        if len(Publication.query.filter_by(url=pub['url']).all()) == 0:
            pub['time_scraped'] = datetime.datetime.now()
            pub['scraper_type'] = self.__class__.__name__

            Publication(**pub)
        # else:
        #     raise DuplicateException(pub)

class WBSouthAsia(SiteScraper):
    URL = 'http://www.worldbank.org/en/region/sar/whats-new'
    URL_BASE = 'http://www.worldbank.org'

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
        desc = soupselect.select(article, 'div.description p')
        body = ''

        if len(desc) > 0:
            desc = desc[0]
            body = desc.contents[0]

            if len(desc.contents) > 1:
                body += desc.contents[3].contents[0]

        date_text = soupselect.select(article, '.date')[0].text
        date = re.match('Date: (.+)', date_text).groups()[0]

        self.save({
            'title': title,
            'url': url,
            'body': body,
            'date': self.get_date(date)
        })

class WBEastAsia(WBSouthAsia):
    URL = 'http://www.worldbank.org/en/region/eap/whats-new'

class AsianDevelopmentBank(SiteScraper):
    URL = 'http://feeds.feedburner.com/adb_news'
    RSS = True

    def _scrape_rss(self, items):
        for article in items:
            self.save({
                'title': article['title'],
                'url': article['feedburner_origlink'],
                'body': article['summary'],
                'date': self.get_date(article['published'])
            })                

class ASEAN(SiteScraper):
    URL = 'http://www.asean.org/news'
    URL_BASE = 'http://www.asean.org'

    def _next_link(self, soup):
        return self.URL_BASE + soupselect.select(
            soup, 'div.pagination-bg a.next')[0]['href']

    def _get_items(self, soup):
        return soupselect.select(soup, 'div.teaser-item')

    def _process_item(self, item):
        title = item.find('h1').text
        url = self.URL_BASE + item.find('h1').find('a')['href']
        rough_date = item.find('p').text
        body = unicode(soupselect.select(item, 'div.pos-content')[0])

        m = re.search('(\d{2} \w+ \d{4})', rough_date)
        date = self.get_date(m.groups()[0])

        self.save({
            'title': title,
            'url': url,
            'body': body,
            'date': date
        })

# TODO: broken feed        
class GlobalDevelopmentNetworkEAsia(SiteScraper):
    URL = 'http://feeds.feedburner.com/gdnet/eastasia'
    RSS = True

    def _scrape_rss(self, items):
        for item in items:
            print a

# TODO: broken feed            
class GlobalDevelopmentNetworkSAsia(SiteScraper):
    URL = 'http://feeds.feedburner.com/gdnet/southasia'
    RSS = True

class UNESCAP(SiteScraper):
    URL = 'http://www.unescap.org/media-centre/feature-stories'
    URL_BASE = 'http://www.unescap.org'

    def _get_items(self, soup):
        return soupselect.select(soup, 'div.view-mode-feature_story .group-right')

    def _process_item(self, item):
        title = item.find('h2').find('a').text
        url = self.URL_BASE + item.find('h2').find('a')['href']
        date = self.get_date(soupselect.select(
            item, '.date-display-single')[0].text)
        body = soupselect.select(item, '.field-name-body p')[0].text

        self.save({
            'title': title,
            'url': url,
            'body': body,
            'date': date
        })

class FAOAsia(SiteScraper):
    URL = 'http://www.fao.org/asiapacific/rap/home/news/rss/en/?type=334'
    RSS = True

    def _scrape_rss(self, items):
        for item in items:
            title = item['title']
            url = item['guid']
            date = item['published_parsed']
            body = item['summary']

            self.save({
                'title': title,
                'url': url,
                'body': body,
                'date': self.get_date(date)
            })

class SEARCA(SiteScraper):
    URL = 'http://www.searca.org/index.php/news'
    URL_BASE = 'http://www.searca.org'

    def _next_link(self, soup):
        return self.URL_BASE + soupselect.select(
            soup, 'a[title=Next]')[0]['href']

    def _get_items(self, soup):
        tables = soupselect.select(soup, 'table.contentpaneopen')        
        return zip(*2 * [ iter(tables) ])

    def _process_item(self, item):
        title = item[0].find('a').text
        url = item[0].find('a')['href']

        try:
            body = item[1].find_all('p')[-1].text

        # Sometimes the content is in a <p> tag, sometimes not
        except:
            body = item[1].find('td').text

        # Articles have no published date
        date = datetime.datetime.now()

        self.save({
            'title': title,
            'url': url,
            'body': body,
            'date': date
        })

# TODO: ask about content            
class TDRI(SiteScraper):
    pass

class CACAARI(SiteScraper):
    URL = 'http://www.cacaari.org/news/rss'
    RSS = True

    def _scrape_rss(self, items):
        for item in items:
            self.save({
                'title': item['title'],
                'url': item['guid'],
                'date': self.get_date(item['published_parsed']),
                'body': item['summary']
            })                

# TODO: can't load site
class VCIEP(SiteScraper):
    pass

# RSS doesn't actually include parseable event dates
class APARRIEventScraper(SiteScraper):
    URL = 'http://www.apaari.org/events/feed/'
    RSS = True

    def _scrape_rss(self, items):
        for item in items:
            self.save_event({
                'title': item['title'],
                'url': item['link'],
                'date': self.get_date(item['published_parsed']),
                'body': item['summary']
            })

class UNESCAPEventScraper(SiteScraper):
    URL = 'http://www.unescap.org/events/upcoming'
    URL_BASE = 'http://www.unescap.org'

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

        self.save_event({
            'title': title,
            'url': url,
            'start_time': start_time,
            'end_time': end_time,
            'body': body
        })

class WBSouthAsiaPubScraper(SiteScraper):
    URL = 'http://wbws.worldbank.org/feeds/xml/sar_all.xml'
    RSS = True

    def _scrape_rss(self, items):
        for item in items:
            self.save_pub({
                'title': item['title'],
                'url': item['link'],
                'date': self.get_date(item['published_parsed']),
                'body': item['summary']
            })

class WBEastAsiaPubScraper(WBSouthAsiaPubScraper):
    URL = 'http://wbws.worldbank.org/feeds/xml/eap_all.xml'

class ADBAgriculturePubScraper(SiteScraper):
    URL = 'http://www.adb.org/publications/search/448'
    URL_BASE = 'http://www.adb.org'

    def _next_link(self, soup):
        return self.URL_BASE + soupselect.select(
            soup, 'li.pager-next a')[0]['href']

    def _get_items(self, soup):
        return soupselect.select(soup, 'div.views-row')

    def _process_item(self, item):
        title = item.find('h3').find('a').text
        url = item.find('h3').find('a')['href']
        date = self.get_date(soupselect.select(item, 'span.date-display-single')[0].text)
        body = soupselect.select(item, 'div.views-field-nothing-1 p')[0].text

        self.save_pub({
            'title': title,
            'url': url,
            'date': date,
            'body': body
        })

class ADBPovertyPubScraper(ADBAgriculturePubScraper):
    URL = 'http://www.adb.org/publications/search/211'

class UNESCAPPubScraper(SiteScraper):
    URL = 'http://www.unescap.org/publications'
    URL_BASE = 'http://www.unescap.org'

if __name__ == '__main__':
    scrapers = [

        # Articles
        'WBSouthAsia',
        'WBEastAsia',
        'AsianDevelopmentBank',
        'ASEAN',
        'UNESCAP',
        'FAOAsia',
        'SEARCA',
        'CACAARI',

        # Events
        'APARRIEventScraper',
        'UNESCAPEventScraper',

        # Pubs
        'WBSouthAsiaPubScraper',
        'WBEastAsiaPubScraper',
        'ADBAgriculturePubScraper',
        'ADBPovertyPubScraper'
    ]

    for s in scrapers:
        globals()[s]().scrape()        
