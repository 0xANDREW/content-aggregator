import os
import json
import datetime

import requests

class DrupalPoster:
    def __init__(self):
        self.__base = os.environ['DRUPAL_BASE']
        self.__user = os.environ['DRUPAL_USER']
        self.__pass = os.environ['DRUPAL_PASS']
        self.__node_path = os.environ['DRUPAL_NODE_PATH']
        self.__login_path = os.environ['DRUPAL_LOGIN_PATH']

        self.__headers = { 'content-type' : 'application/json' }

        self.__login()

    def __url(self, path):
        return '%s/%s' % (self.__base, path)

    def __login(self):
        data = { 'username': self.__user, 'password': self.__pass }

        r = requests.post(self.__url(self.__login_path), 
                          data=json.dumps(data), headers=self.__headers)

        self.__cookies = { r.json()['session_name']: r.json()['sessid'] }
        self.__headers['x-csrf-token'] = r.json()['token']

    def __field_value(self, value, extra=[]):
        for e in extra:
            if type(e) == datetime.datetime:
                value += e.isoformat()
            else:
                value += e

        return { 'und': [{ 'value': value }] }

    # def __field_date_value(self, date):
    #     return { 
    #         'und': [{ 
    #             'value': {
    #                 'date': date.strftime('%m/%d/%Y - %H:%M')
    #             }
    #         }] 
    #     }

    def post(self, thing):
        node_type = thing.__class__.__name__.lower()

        data = {
            'title': thing.title,
            'type': 'article'
        }

        if node_type in ('article', 'publication'):
            data['body'] = self.__field_value(
                thing.body, 
                [ thing.date, thing.url ]
            )

        elif node_type == 'event':
            data['body'] = self.__field_value(
                thing.body, 
                [ thing.start_time, thing.end_time, thing.url ]
            )

        r = requests.post(
            self.__url(self.__node_path),
            data=json.dumps(data),
            headers=self.__headers,
            cookies=self.__cookies
        )

        if r.status_code == requests.codes.ok:
            thing.time_posted = datetime.datetime.now()
        else:
            print r.status_code, r.text

if __name__ == '__main__':
    from model import *
    setup_all()
    create_all()

    d = DrupalPoster()
    
    for p in Article.pending_post():
        print p.title
        d.post(p)

    session.commit()
    
