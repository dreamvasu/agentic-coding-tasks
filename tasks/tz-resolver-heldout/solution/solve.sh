#!/bin/bash
set -euo pipefail

# The bundled tzdata is pinned to 2023c and shadowed via PYTHONPATH=/app, so a
# plain upgrade does not change the registry zoneinfo reads. resolve.py installs
# the current tzdata into a side dir and puts it ahead on sys.path, then resolves
# each zone's offset at its instant.
cp "$(dirname "$0")/resolve.py" /app/resolve.py
python3 /app/resolve.py
