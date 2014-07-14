#!/bin/bash

ENV_FILE=drupal.env
ENV_NAME=agg_env
VENV_PATH=/usr/bin/virtualenv2

# Source environment file
if [ -e "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "$ENV_FILE does not exist"
    exit 1
fi

if [ -e "$ENV_NAME" ]; then
    source "$ENV_NAME/bin/activate"
else
    $VENV_PATH $ENV_NAME
    source "$ENV_NAME/bin/activate"
    pip install -r requirements.txt
fi

python ./feeder.py --no-scrape scrapers.txt

