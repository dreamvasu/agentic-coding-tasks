Our aeromagnetic survey desk is rebuilding its track reductions and the `navkit` package under `/app` is only partly written: the module layout, the data feeds and a small in-repo test suite are in place, but eighteen functions across the package raise `NotImplementedError`. Implement them so one pass over the archive reduces every survey track and writes `/app/report.json`.

The stages form a dependency chain: bearings need declination, leg geometry needs true bearings, closure needs the whole track.

## The package

- Entry point: `python -m navkit reduce` (equivalently `python /app/run_reduction.py`) runs the reduction and writes `/app/report.json`.
- `/app/navkit/config.py` holds every constant: paths, rounding, the earth radius, the closure tolerance. Read it; do not hard-code these values elsewhere.
- `/app/navkit/model.py` defines the `Waypoint` shape every reader must produce, and `/app/navkit/errors.py` the exception types.
- `/app/README.md` lists the module layout.

## The three survey feeds (`/app/data`)

1. `waypoints.csv` - the modern export. Columns `waypoint_id`, `site`, `lat_deg`, `lon_deg`, `altitude_km`, `obs_date` (`YYYY-MM-DD`), `magnetic_bearing_deg`, `leg_km`.
2. `flightlog.dat` - the pre-2016 legacy archive. A fixed-field export with `;;` comment lines; latitude and longitude are degrees/minutes/seconds with a hemisphere letter. The exact column layout is documented in the file's own header comment.
3. `tiein.json` - tie-in reference stations, under a `stations` array, with the same fields as the CSV.

Every waypoint from all three feeds takes part in the reduction.

## What the reduction must compute

- The magnetic declination at each waypoint's position, altitude and observation date. Declination is the angle from true north to magnetic north, positive when magnetic north lies east of true north. The survey desk signs tracks off against the International Geomagnetic Reference Field generation that is currently in force, so each declination must be the value that generation gives for the waypoint's date, and it is checked to 0.05 degrees.
- The true bearing for each waypoint's recorded magnetic bearing, normalised into `[0, 360)`.
- Each track's closure error. A track is flown as a loop. Start at the track's first waypoint, then take that track's waypoints in ascending `waypoint_id` order and run each waypoint's own recorded leg in turn, as a great-circle step from the position reached so far, along that waypoint's true bearing. Every waypoint's leg is run, including the first waypoint's, so a single-waypoint track runs exactly one leg. The closure error is the great-circle distance in kilometres between the track's first waypoint and the position reached after the last leg; the desk signs a track off when that error is within the closure tolerance in `config.py`.

## The report

`python -m navkit reduce` must write `/app/report.json` as a single JSON object with exactly these fields:

- `waypoint_count`: total number of waypoints across all three feeds, as an integer.
- `total_leg_km`: the sum of `leg_km` over every waypoint, reported as an integer. Every `leg_km` in these feeds is already a whole number of kilometres, so no rounding choice arises.
- `sites`: a sorted list of the distinct site names.
- `declination_by_id`: an object mapping every `waypoint_id` to its declination in degrees, rounded to the configured number of decimals.
- `true_bearing_by_id`: an object mapping every `waypoint_id` to its true bearing in degrees, rounded to the configured number of decimals.
- `closure_km_by_site`: an object mapping each site to that track's closure error in kilometres, rounded to the configured number of decimals.

Write only the JSON object to `/app/report.json`.
