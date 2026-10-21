#!/bin/bash
set -euo pipefail
# The eighteen stubs are implemented in solution/navkit_ref/ and copied over the package.
# The one non-obvious step is the field evaluation: the image pins an old ppigrf and
# shadows it on PYTHONPATH, so `pip install -U ppigrf` cannot change the coefficient set
# the import resolves to. Install the generation currently in force into a side directory
# that the package itself prefers, then run the mandated entry point.
REF="$(cd "$(dirname "$0")" && pwd)/navkit_ref"
cp "$REF"/*.py /app/navkit/ 2>/dev/null || true
for d in io geo field nav report; do cp "$REF/$d"/*.py "/app/navkit/$d/" 2>/dev/null || true; done

pip install --quiet --target /app/igrf-current "ppigrf==2.1.0" >/dev/null 2>&1

cd /app && python3 -m navkit reduce
