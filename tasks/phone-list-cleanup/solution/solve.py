"""Reference solution: audit /app/contacts.csv into /app/report.json.

The image pins phonenumbers 8.13.52 and relocates it to /app so PYTHONPATH keeps
that copy in front of anything pip installs. Its bundled numbering-plan metadata
is stale for several regions whose plans changed in 2023-2025 (e.g. Benin's
2024-11-30 8->10 digit migration, Chile's 600 range, Saudi 0811, Laos 030 mobile
reclassification, the Ghana 'AT' carrier rebrand), so validity/type/carrier come
out silently wrong for those rows while the row count still reconciles.

There is no way to recompute a country's numbering plan by hand, so the fix is to
judge each number against current metadata: install the up-to-date phonenumbers
into a side directory and put it AHEAD of the /app-shadowed copy on sys.path (a
plain upgrade is not enough because PYTHONPATH=/app wins).
"""
import csv
import json
import subprocess
import sys

_CURRENT = "/tmp/phonenumbers_current"
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-q", "--target", _CURRENT, "phonenumbers==9.0.34"]
)
sys.path.insert(0, _CURRENT)  # ahead of PYTHONPATH=/app, so the current metadata wins

import phonenumbers  # noqa: E402
from phonenumbers import carrier  # noqa: E402

TYPE_NAMES = {
    getattr(phonenumbers.PhoneNumberType, n): n
    for n in dir(phonenumbers.PhoneNumberType)
    if not n.startswith("_") and isinstance(getattr(phonenumbers.PhoneNumberType, n), int)
}

with open("/app/contacts.csv", newline="") as f:
    rows = list(csv.DictReader(f))

valid_count = 0
type_hist = {}
carrier_by_id = {}
invalid_ids = []
for r in rows:
    rid, raw = r["id"], r["raw_number"]
    region = r.get("default_region") or None
    try:
        num = phonenumbers.parse(raw, region)
        is_valid = phonenumbers.is_valid_number(num)
    except Exception:
        is_valid, num = False, None
    if not is_valid:
        invalid_ids.append(rid)
        continue
    valid_count += 1
    ntype = phonenumbers.number_type(num)
    type_hist[TYPE_NAMES.get(ntype, "UNKNOWN")] = type_hist.get(TYPE_NAMES.get(ntype, "UNKNOWN"), 0) + 1
    if ntype == phonenumbers.PhoneNumberType.MOBILE:
        carrier_by_id[rid] = carrier.name_for_number(num, "en")

report = {
    "total_numbers": len(rows),
    "valid_count": valid_count,
    "invalid_ids": sorted(invalid_ids),
    "type_histogram": dict(sorted(type_hist.items())),
    "carrier_by_id": dict(sorted(carrier_by_id.items())),
}

with open("/app/report.json", "w") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
