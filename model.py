import sys

sys.path.append('elixir')
from elixir import *

# metadata.bind.echo = True

def change_db(db):
    metadata.bind = 'sqlite:///%s' % db

class DrupalBase:
    @classmethod
    def pending_post(cls):
        return cls.query.filter_by(time_posted=None).all()

    @classmethod
    def set_all_pending(cls):
        for thing in cls.query.all():
            thing.time_posted = None

        session.commit()

class Article(DrupalBase, Entity):
    title = Field(Unicode)
    url = Field(Unicode)
    body = Field(UnicodeText)
    date = Field(DateTime)
    time_scraped = Field(DateTime)
    time_posted = Field(DateTime)
    scraper_type = Field(Unicode)
    
class Event(DrupalBase, Entity):
    title = Field(Unicode)
    url = Field(Unicode)
    body = Field(UnicodeText)
    date = Field(DateTime)
    time_scraped = Field(DateTime)
    time_posted = Field(DateTime)
    start_time = Field(DateTime)
    end_time = Field(DateTime)
    scraper_type = Field(Unicode)
    
class Publication(DrupalBase, Entity):
    title = Field(Unicode)
    url = Field(Unicode)
    body = Field(UnicodeText)
    date = Field(DateTime)
    time_scraped = Field(DateTime)
    time_posted = Field(DateTime)
    scraper_type = Field(Unicode)
