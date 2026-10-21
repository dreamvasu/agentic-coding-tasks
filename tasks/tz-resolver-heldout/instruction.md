Our scheduling service stamps every cross-region event with the local UTC offset of the site it belongs to, and last week's rollout put several events on the wrong offset. I need an offset resolver I can trust for any of our sites, not just the ones in the sample. The sample is at `/app/locations.csv` with columns `location_id`, `zone` (an IANA time-zone name like `Europe/Berlin`), and `instant_utc` (a UTC instant in ISO 8601, e.g. `2025-06-15T09:00:00Z`). Every zone in the batch is a real IANA zone.

Write `/app/resolve.py` exposing a function `resolve(zone, instant)`:

- `zone` is an IANA time-zone name (a string).
- `instant` is a UTC instant as an ISO 8601 string ending in `Z`.
- Return that zone's UTC offset **in effect at that instant** as a string of the form `+HH:MM` or `-HH:MM` (sign always present, two-digit hours and minutes, e.g. `+05:00`, `-03:00`, `+05:30`, `+00:00`).

Then run `resolve` over every row of `/app/locations.csv` and write `/app/offsets.json`: a JSON object mapping each `location_id` to the offset string `resolve` returns for that row's `zone` and `instant_utc`.

Each offset has to be right. Keep `resolve` importable: define it and any helpers at module level and do no work on import (guard the file reading and the write to `/app/offsets.json` under `if __name__ == "__main__":`). The resolver is imported and called directly against zones and instants beyond the sample, so it has to be correct for any IANA zone and instant, not only the rows in the sample. Write only the JSON object to `/app/offsets.json` and nothing else.
