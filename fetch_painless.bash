#!/usr/bin/env bash

# Enable exit-on-error, and command log
set -xe

PAINLESS_ZIP=painless-v2.zip
PAINLESS_URL=http://www.lrde.epita.fr/dload/painless/painless-v2.zip
PAINLESS_DIR=painless-v2

if [[ ! -a $PAINLESS_DIR ]]
then
    if [[ ! -a $PAINLESS_ZIP ]]
    then
        wget $PAINLESS_URL
    fi
    unzip $PAINLESS_ZIP
fi


