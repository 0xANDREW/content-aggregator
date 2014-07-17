ReSAKSS Content Aggregator
==========================

Drupal Instance Preparation
---------------------------

### Required Modules
* `services` 
* `libraries` (upgrade to >= 2.2)

### Steps
1. Enable `services` module
2. Enable `REST Server` module
3. Add service endpoint (`/admin/structure/services/add`)
    1. Name: `api`
    2. Server: `REST`
    3. Path: `api`
    4. Session authentication: checked
4. Edit endpoint resources (/admin/structure/services/list/api/resources)
    1. Enable `node/create` resource
    2. Enable `user/login` resource
5. Edit endpoint REST parameters (/admin/structure/services/list/api/server)
    1. Response formatters: `json` only
    2. Request parsing: `application/json` only
6. Create user `feed` with `developer` role

### Notes
* All uploaded items are unpublished by default
* Date limit is January 1, 2010
* Once a dupliacte item is detected, the scrape for that feed is aborted

Running the Aggregator
----------------------

### Requirements
* Python 2.7
* `virtualenv` library for Python
* `sqlite3` system library

### Steps  
1. Edit `drupal.env.sample` in the source tree to match your instance's parameters
2. Save as `drupal.env`
3. Execute `run.sh` from the project root

### Command-line Options (to `run.sh`)
* `--no-scrape`: skip content scraping
* `--no-post`: skip content upload
* `--post-limit N`: only upload the first N items to Drupal
* `--debug`: show debug info

### Notes
* The scraping process takes 1-2 hours to run the first time. Subsequent runs take much less time since the process aborts the feed as soon as it finds a duplicate URL. The time required to post all the items to Drupal depends on the number of items scraped.
* If it's going to be a `cron` job, ensure that `run.sh` is run from the project root.
  
