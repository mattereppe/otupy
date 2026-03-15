#!/bin/bash
#
# Automatically restart connector.py on changes of the configuration files
PYTHON=python3
CONNECTOR=connector.py

watchmedo auto-restart --patterns="*.yaml" --recursive -- $PYTHON $CONNECTOR
