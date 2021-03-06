#!/bin/bash

ENV_FILE=drupal.env
ENV_NAME=agg_env
VENV_PATH=/usr/bin/virtualenv2

# For systems where Python 2.x is default,
# adjust path
if [ ! -e "$VENV_PATH" ]; then
    VENV_PATH=/usr/bin/virtualenv
fi

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

python ./feeder.py scrapers.txt "$@"
