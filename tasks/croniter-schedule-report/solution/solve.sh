#!/bin/bash
# Reference solution. The report is only correct if croniter's backward iteration is correct.
# croniter 6.2.0's proc_day_of_month backward branch computes the previous month's length from
# a STATIC table (February always 28), so a "29th of every month" schedule skips Feb 29 in leap
# years and get_prev returns the January run instead. That silently corrupts the billing_eom29
# job's fire times. We apply the upstream 6.2.1 fix (leap-aware _last_day_of_month), then generate
# the report from the provided schedules.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
SRC="$APP_ROOT/croniter/croniter.py"

python3 - "$SRC" <<'PY'
import sys, io
path = sys.argv[1]
src = io.open(path, encoding="utf-8").read()
old = "                    days_in_prev_month = DAYS[(month - 2) % self.MONTHS_IN_YEAR]\n"
new = ("                    prev_month = (month - 2) % self.MONTHS_IN_YEAR + 1\n"
       "                    prev_year = year - 1 if month == 1 else year\n"
       "                    days_in_prev_month = _last_day_of_month(prev_year, prev_month)\n")
if old not in src:
    sys.exit("solve.sh: expected buggy line not found")
io.open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))
print("solve.sh: patched croniter backward month-length")
PY

python3 - <<'PY'
import json, datetime
from croniter import croniter
ref = datetime.datetime(2024, 3, 15, 12, 0, 0)
scheds = json.load(open("/app/schedules.json"))
report = {}
for name, expr in scheds.items():
    it = croniter(expr, ref)
    fires = [it.get_prev(datetime.datetime) for _ in range(3)]
    report[name] = [f.isoformat() for f in fires]
json.dump(report, open("/app/report.json", "w"), indent=2)
print("solve.sh: wrote /app/report.json")
PY
