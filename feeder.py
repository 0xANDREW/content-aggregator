import sys
import argparse
import logging
import os

import scraper
import uploader
from model import *

global MODULE_LOG_LEVEL
MODULE_LOG_LEVEL = logging.INFO
PROGRESS_INTERVAL = 500

logger = None

def setup_loggers():
    global logger

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s %(message)s'))
    ch.setLevel(MODULE_LOG_LEVEL)

    logger = logging.getLogger(__name__)
    logger.setLevel(MODULE_LOG_LEVEL)
    logger.addHandler(ch)

    logging.getLogger('scraper').setLevel(MODULE_LOG_LEVEL)
    logging.getLogger('uploader').setLevel(MODULE_LOG_LEVEL)

def do_post(poster, things, limit=None):
    progress = 1
    num_things = len(things)

    logger.info('Posting %s (%d)...' % 
                 (things[0].__class__.__name__, num_things))

    for thing in things:
        logger.debug('%d/%d...' % (progress, num_things))
        
        d.post(thing)
        progress += 1        

        if limit and progress >= limit:
            logger.info('Post limit reached (%d)' % limit)
            return

        if progress % PROGRESS_INTERVAL == 0:
            logger.debug('Progress: %d/%d' % (progress, len(things)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('scrapers')
    parser.add_argument('--no-scrape', action='store_true')
    parser.add_argument('--no-post', action='store_true')
    parser.add_argument('--post-limit', type=int)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--db', default='db/scraper.sqlite')
    parser.add_argument('--kill-db', action='store_true')
    parser.add_argument('--events-only', action='store_true')
    parser.add_argument('--pubs-only', action='store_true')
    parser.add_argument('--show-pending', action='store_true')
    parser.add_argument('--set-all-pending', action='store_true')
    parser.add_argument('--only')
    args = parser.parse_args()

    if args.debug:
        MODULE_LOG_LEVEL = logging.DEBUG

    setup_loggers()

    if args.kill_db:
        try:
            os.unlink(args.db)
        except:
            logger.warning('Database %s does not exist' % args.db)

    logger.info('Using DB %s' % args.db)

    change_db(args.db)        
    setup_elixir()

    if args.set_all_pending:
        for cls in [ Article, Event, Publication ]:
            cls.set_all_pending()

        logger.info('Set all things pending')
        sys.exit()

    if args.show_pending:
        for cls in [ Article, Event, Publication ]:
            print '%s: %d' % (cls.__name__, len(cls.pending_post()))

        sys.exit()

    if not args.no_scrape:
        with open(args.scrapers) as f:
            scrapers = map(lambda s: s.strip(), list(f))

        if args.only:
            scrapers = args.only.split(',')

        for s in scrapers:

            # Python-style comments available for scrapers.txt
            if not s.startswith('#'):
                getattr(scraper, s)().scrape()
    else:
        logger.info('Skipping scrape')

    if not args.no_post:
        if args.post_limit:
            logger.info('Post limit: %d' % args.post_limit)

        try:
            d = uploader.DrupalPoster()
        except Exception, e:
            logger.error(e)
            logger.error('Login error, exiting')
            sys.exit(1)

        classes = [ Article, Event, Publication ]

        if args.events_only:
            classes = [ Event ]

        if args.pubs_only:
            classes = [ Publication ]

        for cls in classes:
            things = cls.pending_post()            

            if len(things) == 0:
                logger.warning('No pending items for %s' % cls.__name__)
            else:
                do_post(d, things, args.post_limit)

    else:
        logger.info('Skipping post')

