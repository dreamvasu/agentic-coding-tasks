#!/bin/bash
set -euo pipefail

# Reference solution. Logic in solve.py: source current numbering-plan metadata
# (phonenumbers 9.0.34 ahead of the /app-shadowed 8.13.52), then audit the list.
python3 "$(dirname "$0")/solve.py"
