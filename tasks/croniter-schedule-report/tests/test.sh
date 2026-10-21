#!/bin/bash
# Verifier: read the agent's /app/report.json and check every job's three fire times against the
# correct values (computed independently; the correct previous-3 runs before 2024-03-15T12:00:00).
# The discriminating job is billing_eom29 ("0 0 29 * *"): the most recent 29th before the reference
# in a leap year is 2024-02-29, which croniter 6.2.0 silently skips. Datetimes are compared as
# parsed values (format-tolerant). Pure bash + system python.
set -uo pipefail
LOGV="${LOGV:-/logs/verifier}"; mkdir -p "$LOGV"; PYBIN="${PYBIN:-python}"

out="$("$PYBIN" - <<'PY' 2>&1
import sys, json, datetime
P = "/app/report.json"
try:
    rep = json.load(open(P))
except Exception as e:
    print("VERIFIER-FAIL: cannot read /app/report.json:", e); sys.exit(1)

expected = {
  "billing_eom29": ["2024-02-29T00:00:00", "2024-01-29T00:00:00", "2023-12-29T00:00:00"],
  "quarter_hours": ["2024-03-15T10:15:00", "2024-03-15T08:15:00", "2024-03-15T06:15:00"],
  "weekday_open":  ["2024-03-15T09:00:00", "2024-03-14T09:00:00", "2024-03-13T09:00:00"],
  "month_start":   ["2024-03-01T00:00:00", "2024-02-01T00:00:00", "2024-01-01T00:00:00"],
  "sat_backup":    ["2024-03-09T06:30:00", "2024-03-02T06:30:00", "2024-02-24T06:30:00"],
  "midmonth":      ["2024-02-15T12:00:00", "2024-01-15T12:00:00", "2023-12-15T12:00:00"],
}
def parse(s):
    return datetime.datetime.fromisoformat(str(s).strip().replace("Z","").replace(" ","T"))

fails = []
if not isinstance(rep, dict):
    print("VERIFIER-FAIL: report.json is not a JSON object"); sys.exit(1)
for name, exp in expected.items():
    if name not in rep:
        fails.append(f"{name}: missing from report"); continue
    got = rep[name]
    if not isinstance(got, list) or len(got) != 3:
        fails.append(f"{name}: expected 3 entries, got {got!r}"); continue
    try:
        gv = [parse(x) for x in got]
    except Exception as e:
        fails.append(f"{name}: unparseable datetime ({e})"); continue
    ev = [parse(x) for x in exp]
    if gv != ev:
        fails.append(f"{name}: got {[d.isoformat() for d in gv]}, expected {exp}")

if fails:
    print("VERIFIER-FAIL:", " | ".join(fails)); sys.exit(1)
print("VERIFIER-PASS: all jobs report correct fire times (including the leap-February boundary)")
sys.exit(0)
PY
)"
rc=$?
echo "$out"
if [ "$rc" -eq 0 ] && [[ "$out" == *"VERIFIER-PASS"* ]]; then echo 1 > "$LOGV/reward.txt"; else echo 0 > "$LOGV/reward.txt"; fi
