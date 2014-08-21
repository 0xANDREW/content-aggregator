import time
import os
import json
import datetime
import logging

import requests

from model import *

logging.getLogger('requests').setLevel(logging.WARNING)

MODULE_LOG_LEVEL = logging.DEBUG

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s %(message)s'))
ch.setLevel(MODULE_LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(MODULE_LOG_LEVEL)
logger.addHandler(ch)

class DrupalPoster:
    CONTENT_TYPE_MAP = {
        'article': 'blog_post',
        'event': 'event',
        'publication': 'resource'
    }

    BODY_TEMPLATE = """%s

    Originally published on %s. Please click the following URL for more info: %s
    """

    MAX_TITLE_LEN = 220
    DATE_FMT = '%m/%d/%Y'
    PUB_TYPE = '608'
    REQ_TIMEOUT = 120
    REQ_DELAY = 60
    MAX_TRIES = 10

    def __init__(self):
        self.__base = os.environ['DRUPAL_BASE']
        self.__api_path = os.environ['DRUPAL_API_PATH']
        self.__user = os.environ['DRUPAL_USER']
        self.__pass = os.environ['DRUPAL_PASS']
        self.__node_path = os.environ['DRUPAL_NODE_PATH']
        self.__login_path = os.environ['DRUPAL_LOGIN_PATH']

        self.__headers = { 'content-type' : 'application/json' }
        self.__cookies = {}

        self.__visit_home()
        self.__login()

    def __url(self, path):
        return '%s/%s/%s' % (self.__base, self.__api_path, path)

    def __request(self, path='', data={}, method='post'):
        tries = 0

        # Retry POST request N times
        while 1:
            try:
                if method == 'get':
                    r = requests.get(self.__base, timeout=self.REQ_TIMEOUT)
                else:
                    r = requests.post(self.__url(path), 
                                      data=json.dumps(data), 
                                      headers=self.__headers,
                                      cookies=self.__cookies,
                                      timeout=self.REQ_TIMEOUT
                                  )

                r.raise_for_status()
                
                return r

            except requests.exceptions.HTTPError, e:

                # Throw exception again on auth error
                if r.status_code == requests.codes.unauthorized:
                    logger.error('Invalid user/pass')
                    raise e

                # Warn on content/server error
                else:
                    logger.warning(e)
                    return r

            # Retry on connection error
            except requests.exceptions.ConnectionError, e:
                tries += 1

                # Throw exception after max tries
                if tries == self.MAX_TRIES:
                    logger.error('Max request attempts exceeded')
                    raise e

                logger.warning('Connection error (%d/%d), retrying...' 
                               % (tries, self.MAX_TRIES))

                time.sleep(self.REQ_DELAY)        

    def __visit_home(self):
        logger.debug('Visting home page (%s)...' % self.__base)

        self.__request(method='get')

    def __login(self):
        logger.info('Logging in to Drupal (%s)...' % self.__base)

        data = { 'username': self.__user, 'password': self.__pass }

        r = self.__request(self.__login_path, data)

        self.__cookies = { r.json()['session_name']: r.json()['sessid'] }
        self.__headers['x-csrf-token'] = r.json()['token']

    # Append original date and URL to body
    def __body(self, body, date, url):
        date_text = date.strftime(self.DATE_FMT) if date else ''

        return { 
            'und': [{ 
                'value': self.BODY_TEMPLATE % (body, date_text, url) 
            }] 
        }

    def post(self, thing):
        node_type = self.CONTENT_TYPE_MAP[thing.__class__.__name__.lower()]

        data = {
            'title': thing.title[:self.MAX_TITLE_LEN],
            'type': node_type,
            'body': self.__body(thing.body, thing.date, thing.url),
            'status': None
        }

        # Custom structure required for custom fields
        if node_type == 'resource':
            data['field_publication_type'] = {
                'und': [ self.PUB_TYPE ]
            }

            if thing.date:
                data['field_publication_date'] = {
                    'und': [{ 
                        'value': { 
                            'date': thing.date.strftime('%Y')
                        }
                    }]
                }

        elif node_type == 'event':
            if thing.start_time:
                value = thing.start_time.strftime(self.DATE_FMT)
                value2 = thing.end_time.strftime(self.DATE_FMT) if thing.end_time else None

                data['field_event_date'] = {
                    'und': [{ 
                        'value': { 
                            'date': value
                        },
                        'value2': {
                            'date': value2
                        }
                    }]
                }

        r = self.__request(self.__node_path, data)

        if r.status_code == requests.codes.ok:
            thing.time_posted = datetime.datetime.now()
            session.commit()
