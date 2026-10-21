#!/bin/sh
# Survey desk reduction entry point.
set -e
cd /app
python -m navkit reduce
