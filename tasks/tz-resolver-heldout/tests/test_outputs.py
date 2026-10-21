"""Verifier for the UTC-offset resolver at /app/resolve.py.

The agent writes /app/resolve.py and produces /app/offsets.json for the visible
sample. This verifier checks that file, then imports the agent's /app/resolve.py
and calls its resolve() directly against a held-out set of (zone, instant) pairs
the agent never sees (embedded below, not present anywhere in /app). Each expected
offset is the value the CURRENT tz database resolves.

The visible sample is confined to zones whose offset did not change, so a resolver
built on the image's pinned, PYTHONPATH-shadowed tzdata 2023c self-verifies on the
sample. The held-out set adds zones that changed their standing offset or DST rule
after the 2023c cutoff (Kazakhstan's Almaty/Qostanay unified to +05, Paraguay went
to permanent -03, Greenland's Scoresbysund shifted, the Antarctic stations Casey
and Vostok re-based); the stale registry returns the pre-change offset for those
and mismatches here, while the control zones in the held-out set still match.
Standard library only.
"""
import json
import sys
from pathlib import Path

import pytest

APP = "/app"
OFFSETS = Path("/app/offsets.json")

# Reference offsets for the 12 visible rows in /app/locations.csv (current tz db).
VISIBLE_EXPECTED = {
    "L01": "+01:00", "L02": "+02:00", "L03": "-04:00", "L04": "-06:00",
    "L05": "+09:00", "L06": "+05:30", "L07": "+11:00", "L08": "+03:00",
    "L09": "-03:00", "L10": "+12:00", "L11": "+08:00", "L12": "+01:00",
}

# Held-out (zone, UTC instant, expected current offset). Never shipped to the
# agent. The first block is zones that changed after the pinned tzdata's cutoff
# (the stale registry returns the pre-change offset); the second block is control
# zones that did not change (the stale registry still gets these right, so the
# failures isolate to the changed data, not to the resolver's logic).
HELDOUT = [
    ("Asia/Almaty", "2025-03-20T00:00:00Z", "+05:00"),
    ("Asia/Almaty", "2025-08-01T12:00:00Z", "+05:00"),
    ("Asia/Qostanay", "2025-05-10T09:00:00Z", "+05:00"),
    ("Asia/Qostanay", "2025-11-02T06:00:00Z", "+05:00"),
    ("America/Asuncion", "2025-06-15T12:00:00Z", "-03:00"),
    ("America/Asuncion", "2025-05-01T00:00:00Z", "-03:00"),
    ("America/Asuncion", "2025-08-20T15:00:00Z", "-03:00"),
    ("America/Scoresbysund", "2025-02-01T12:00:00Z", "-02:00"),
    ("America/Scoresbysund", "2025-08-01T12:00:00Z", "-01:00"),
    ("Antarctica/Casey", "2025-06-15T00:00:00Z", "+08:00"),
    ("Antarctica/Casey", "2025-01-10T00:00:00Z", "+08:00"),
    ("Antarctica/Vostok", "2025-06-15T00:00:00Z", "+05:00"),
    ("Antarctica/Vostok", "2025-12-05T00:00:00Z", "+05:00"),
    # control zones (unchanged since the pinned cutoff)
    ("Europe/Paris", "2025-07-01T12:00:00Z", "+02:00"),
    ("America/Los_Angeles", "2025-07-01T12:00:00Z", "-07:00"),
    ("Asia/Dubai", "2025-07-01T12:00:00Z", "+04:00"),
    ("Asia/Kolkata", "2025-12-01T12:00:00Z", "+05:30"),
    ("America/New_York", "2025-12-15T12:00:00Z", "-05:00"),
    ("Australia/Sydney", "2025-07-01T12:00:00Z", "+10:00"),
    ("Pacific/Chatham", "2025-06-15T12:00:00Z", "+12:45"),
    ("Asia/Tehran", "2025-06-15T12:00:00Z", "+03:30"),
]


def _norm(value):
    """Accept the required +HH:MM / -HH:MM form; normalize a bare '+00:00' vs
    '-00:00' so a zero offset compares equal regardless of sign."""
    s = str(value).strip()
    return "+00:00" if s in ("-00:00", "+00:00") else s


@pytest.fixture(scope="module")
def resolve_fn():
    """Import the agent's /app/resolve.py and hand back its resolve() callable.
    resolve must be importable with no side effects (instruction: guard file work
    under __main__)."""
    if APP not in sys.path:
        sys.path.insert(0, APP)
    sys.modules.pop("resolve", None)
    try:
        import resolve as resolve_mod
    except Exception as e:
        pytest.fail(f"could not import /app/resolve.py: {e!r}")
    assert hasattr(resolve_mod, "resolve"), "/app/resolve.py does not define resolve()"
    assert callable(resolve_mod.resolve), "/app/resolve.py: resolve is not callable"
    return resolve_mod.resolve


def test_offsets_json_matches_visible():
    """/app/offsets.json exists and is the object the resolver should produce for
    the visible sample at /app/locations.csv (instruction: map each location_id to
    its offset string)."""
    assert OFFSETS.exists(), "/app/offsets.json does not exist"
    try:
        data = json.loads(OFFSETS.read_text(encoding="utf-8"))
    except Exception as e:
        pytest.fail(f"/app/offsets.json is not valid JSON: {e}")
    assert isinstance(data, dict), f"offsets.json must be a JSON object, got {type(data).__name__}"
    mism = []
    for lid, expected in VISIBLE_EXPECTED.items():
        if lid not in data:
            mism.append(f"{lid}: missing")
        elif _norm(data[lid]) != _norm(expected):
            mism.append(f"{lid}: got {data.get(lid)!r}, expected {expected!r}")
    assert not mism, "offsets.json differs from the reference:\n" + "\n".join(mism[:15])


def test_heldout_offsets(resolve_fn):
    """Call the agent's resolve() on (zone, instant) pairs it never saw. Every
    offset must equal what the current tz database resolves; a resolver built on
    the stale bundled tzdata returns the pre-change offset for the changed zones
    and fails many of these."""
    mismatches = []
    for zone, instant, expected in HELDOUT:
        try:
            got = resolve_fn(zone, instant)
        except Exception as e:
            mismatches.append(f"[{zone} @ {instant}] raised {e!r}")
            continue
        if _norm(got) != _norm(expected):
            mismatches.append(f"[{zone} @ {instant}] got {got!r}, expected {expected!r}")
    assert not mismatches, (
        f"{len(mismatches)} of {len(HELDOUT)} held-out offsets are wrong (the stale "
        f"registry resolves the pre-change offset):\n" + "\n".join(mismatches[:15])
    )
