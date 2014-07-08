from elixir import *

metadata.bind = 'sqlite:///db/resakss.sqlite'
# metadata.bind.echo = True

class Article(Entity):
    title = Field(Unicode)
    url = Field(Unicode)
    body = Field(UnicodeText)
    date = Field(DateTime)
    time_scraped = Field(DateTime)
    time_posted = Field(DateTime)
    scraper_type = Field(Unicode)
    
class Event(Entity):
    title = Field(Unicode)
    url = Field(Unicode)
    body = Field(UnicodeText)
    date = Field(DateTime)
    time_scraped = Field(DateTime)
    time_posted = Field(DateTime)
    start_time = Field(DateTime)
    end_time = Field(DateTime)
    scraper_type = Field(Unicode)
    
class Publication(Entity):
    title = Field(Unicode)
    url = Field(Unicode)
    body = Field(UnicodeText)
    date = Field(DateTime)
    time_scraped = Field(DateTime)
    time_posted = Field(DateTime)
    scraper_type = Field(Unicode)
