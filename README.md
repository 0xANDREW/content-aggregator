Content Aggregator
==========================

Description
----
Combination web scraper and Drupal uploader. The content sources listed below are scraped (raw or via RSS), the entries stored in a local SQLite database, then uploaded to a Drupal instance via the REST API (part of the `services` module). 

Content Sources
---------------------
### World Bank South Asia
* Articles: <http://www.worldbank.org/en/region/sar/whats-new>
* Publications: <http://www.worldbank.org/en/region/sar/research/all?majdocty_exact=Publications+%26+Research&qterm=&lang_exact=English>

### World Bank East Asia
* Articles: <http://www.worldbank.org/en/region/eap/whats-new>
* Publications: <http://www.worldbank.org/en/region/eap/research/all?majdocty_exact=Publications+%26+Research&qterm=&lang_exact=English>

### Asian Development Bank
* Articles (RSS): <http://feeds.feedburner.com/adb_news>
* Publications (RSS): <http://feeds.feedburner.com/adb_publications>

### ASEAN
* Articles: <http://www.asean.org/news>

### UNESCAP
* Articles: <http://www.unescap.org/media-centre/feature-stories>
* Events: <http://www.unescap.org/events/upcoming>
* Publications: <http://www.unescap.org/publications>

### CACARRI
* Articles: <http://www.cacaari.org/en.php?/news>

### APAARI
* Events (RSS): <http://www.apaari.org/events/feed>

### University of Central Asia
* Articles: <http://www.ucentralasia.org/news.asp>

Drupal Instance Preparation
---------------------------

### Required Modules
* `services` 
* `libraries` (upgrade to >= 2.2)

### Steps
1. Enable `services` module
    1. `drush pm-download services && drush pm-enable services`
2. Enable `REST Server` module
    1. `drush pm-enable rest_server`
2. Clear Drupal cache
    1. `drush cc all`
3. Add service endpoint (`/admin/structure/services/add`)
    1. Name: `api`
    2. Server: `REST`
    3. Path: `api`
    4. Session authentication: checked
4. Edit endpoint resources (`/admin/structure/services/list/api/resources`)
    1. Enable `node/create` resource
    2. Enable `user/login` resource
5. Edit endpoint REST parameters (`/admin/structure/services/list/api/server`)
    1. Response formatters: `json` only
    2. Request parsing: `application/json` only
6. Create user `feed` with `developer` role

Running the Aggregator
----------------------

### Requirements
* Python >= 2.6
* `virtualenv` Python library
* `sqlite3` system library

### Steps  
1. Edit `drupal.env.sample` in the source tree to match your instance's parameters
2. Save as `drupal.env`
3. Execute `run.sh` from the project root
    * If the internal scraper database should be cleared, either delete `db/scraper.sqlite` or run the scraper manually for the first time: `./run.sh --kill-db`
    * For `cron`, run it like this (probably at midnight): `cd <scraper dir> && ./run.sh`

### Command-line Options (to `run.sh`)
* `--no-scrape`: skip content scraping
* `--no-post`: skip content upload
* `--post-limit <N>`: only upload the first N items to Drupal
* `--debug`: show debug info
* `--db <db>`: specify database file (default: `db/scraper.sqlite`)
* `--kill-db`: delete database before start
* `--events-only`: only post events to Drupal
* `--pubs-only`: only post pubs to Drupal
* `--show-pending`: print number of pending things
* `--only <scraper>`: only run specified scraper (see `scrapers.txt`)

Notes
-----  
* All uploaded items are unpublished by default.
* Date limit for articles is January 1, 2014 and January 1, 2010 for events and publications.

Known Issues
----
* APAARI Events RSS feed does not include parseable event dates
