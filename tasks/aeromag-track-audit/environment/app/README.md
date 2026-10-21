# navkit

Aeromagnetic survey track reduction.

    python -m navkit reduce      # writes /app/report.json

## Layout

    navkit/io/       three survey feeds (modern CSV, legacy fixed-field log, tie-in JSON)
    navkit/geo/      DMS conversion, great-circle distance, bearing arithmetic
    navkit/field/    reference-field evaluation (declination)
    navkit/nav/      magnetic-to-true correction, leg geometry, track closure
    navkit/report/   payload assembly + serialisation
    tests/           in-repo suite

## Operations

The reduction runs from `ops/reduce.sh` on the survey desk's workstation. Headings
feed the flight-planning system, so declinations are survey-grade: the desk checks
them against the reference field of record before a track is signed off.
