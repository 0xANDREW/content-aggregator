import argparse
import logging

import scraper
import uploader
from model import *

MODULE_LOG_LEVEL = logging.DEBUG
PROGRESS_INTERVAL = 500

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s %(message)s'))
ch.setLevel(MODULE_LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(MODULE_LOG_LEVEL)
logger.addHandler(ch)

setup_all()
create_all()

def do_post(poster, things):
    progress = 0

    logger.info('Posting %s (%d)...' % 
                 (things[0].__class__.__name__, len(things)))

    for thing in things:
        d.post(thing)
        progress += 1

        if progress % PROGRESS_INTERVAL == 0:
            logger.debug('Progress: %d/%d' % (progress, len(things)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('scrapers')
    parser.add_argument('--no-scrape', action='store_true')
    parser.add_argument('--no-post', action='store_true')
    args = parser.parse_args()

    if not args.no_scrape:
        with open(args.scrapers) as f:
            scrapers = map(lambda s: s.strip(), list(f))

        for s in scrapers:
            getattr(scraper, s)().scrape()

    if not args.no_post:
        d = uploader.DrupalPoster()

        do_post(d, Article.pending_post())
        do_post(d, Event.pending_post())
        do_post(d, Publication.pending_post())
