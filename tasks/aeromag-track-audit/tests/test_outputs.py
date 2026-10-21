"""Verifier for the aeromagnetic track reduction.

Only the produced /app/report.json is inspected (standard library only). The
expected values below are the CURRENT reference-field truth: declinations
evaluated against the current IGRF coefficient set, with the true bearings and
track closures that follow from them.

The image pins ppigrf 1.0.0 and relocates it to /app with PYTHONPATH=/app, so the
coefficients the import resolves to are an earlier IGRF generation and a plain
`pip install -U ppigrf` cannot displace them. Those coefficients revise both the
definitive 2020 values and the 2020-2025 secular-variation terms, so every 2024
observation in this archive lands 0.47-0.67 degrees away from the current field --
far outside the 0.05 degree survey tolerance. The counts, leg totals and site list
reconcile either way, so a stale reduction looks complete.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

REPORT = Path("/app/report.json")

# The test runner reaches pytest through an isolated interpreter that does not carry the
# image's site-packages, so a bare "python3" here would resolve to that interpreter and
# fail on `import numpy` before the reduction ever starts. Name the image interpreter
# explicitly instead.
IMAGE_PYTHON = next(
    (p for p in ("/usr/local/bin/python", "/usr/local/bin/python3", "/usr/bin/python3")
     if os.path.exists(p)),
    "python3",
)


def _image_env():
    """The environment the image itself defines, not the test runner's."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP")}
    env["PYTHONPATH"] = "/app"          # matches ENV PYTHONPATH=/app in the Dockerfile
    env["PATH"] = "/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"
    return env


@pytest.fixture(scope="session", autouse=True)
def regenerate_report():
    """Grade the package, not a leftover file.

    The instruction makes `python -m navkit reduce` the entry point that writes the
    report, so the report is discarded and regenerated through that entry point here.
    A run that only leaves a hand-written /app/report.json behind, or whose package
    still raises NotImplementedError, fails at this point rather than being graded on
    an artifact the package never produced.
    """
    if REPORT.exists():
        REPORT.unlink()
    proc = subprocess.run(
        [IMAGE_PYTHON, "-m", "navkit", "reduce"],
        cwd="/app", env=_image_env(), capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, (
        "`python -m navkit reduce` exited %d\n--- stdout ---\n%s\n--- stderr ---\n%s"
        % (proc.returncode, proc.stdout[-4000:], proc.stderr[-4000:])
    )
    assert REPORT.is_file(), "`python -m navkit reduce` did not write /app/report.json"

DECL_TOL = 0.05      # degrees, per the instruction
BEARING_TOL = 0.05   # degrees
CLOSURE_TOL = 0.5    # km

# The instruction requires each reported figure to be rounded to the number of decimals
# config.py configures, which the tolerances above are far too loose to enforce on their
# own. These mirror DECLINATION_DECIMALS / BEARING_DECIMALS / DISTANCE_DECIMALS.
DECL_DECIMALS = 4
BEARING_DECIMALS = 3
DISTANCE_DECIMALS = 3


def _rounding_complaint(label, value, decimals):
    """Non-empty when `value` carries more precision than the report is allowed."""
    if abs(value - round(value, decimals)) > 1e-9:
        return "%s: %r is not rounded to %d decimals" % (label, value, decimals)
    return ""

EXPECTED_DECLINATION = {
    "T001": -15.076,
    "T002": -12.027,
    "W001": -16.0137,
    "W002": -18.3113,
    "W003": -17.5649,
    "W004": -15.411,
    "W005": -17.8027,
    "W006": -18.7534,
    "W007": -18.2084,
    "W008": -15.9153,
    "W009": -20.33,
    "W010": -21.1697,
    "W011": -22.0822,
    "W012": -19.6229,
    "W013": -21.6614,
    "W014": -21.0244,
    "W015": -19.1513,
    "W016": -21.236,
    "W017": -7.9398,
    "W018": -10.1213,
    "W019": -10.3936,
    "W020": -9.3921,
    "W021": -8.8016,
    "W022": -10.8235,
    "W023": -7.511,
    "W024": -7.5275,
}
EXPECTED_TRUE_BEARING = {
    "T001": 262.644,
    "T002": 6.513,
    "W001": 14.056,
    "W002": 242.959,
    "W003": 351.345,
    "W004": 210.489,
    "W005": 194.227,
    "W006": 184.777,
    "W007": 94.942,
    "W008": 268.945,
    "W009": 96.07,
    "W010": 132.2,
    "W011": 96.978,
    "W012": 144.037,
    "W013": 232.839,
    "W014": 247.216,
    "W015": 0.979,
    "W016": 343.344,
    "W017": 347.72,
    "W018": 166.449,
    "W019": 325.596,
    "W020": 224.368,
    "W021": 142.988,
    "W022": 138.337,
    "W023": 241.909,
    "W024": 145.473,
}
EXPECTED_CLOSURE_KM = {
    "KALAHARI": 265.982,
    "NAMAQUA": 164.226,
    "OKAVANGO": 180.082,
    "TIE-ALPHA": 90.0,
    "TIE-BRAVO": 56.0,
}
EXPECTED_WAYPOINT_COUNT = 26
EXPECTED_TOTAL_LEG_KM = 2079
EXPECTED_SITES = ['KALAHARI', 'NAMAQUA', 'OKAVANGO', 'TIE-ALPHA', 'TIE-BRAVO']


@pytest.fixture(scope="module")
def report():
    assert REPORT.exists(), "/app/report.json does not exist"
    try:
        data = json.loads(REPORT.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("/app/report.json is not valid JSON: %s" % exc)
    assert isinstance(data, dict), "report must be a JSON object"
    return data


def test_counts_and_sites(report):
    """Feed coverage: every waypoint from all three feeds took part."""
    assert int(report["waypoint_count"]) == EXPECTED_WAYPOINT_COUNT
    assert int(report["total_leg_km"]) == EXPECTED_TOTAL_LEG_KM
    # The instruction asks for a sorted list, so compare in the order given.
    assert [str(s) for s in report["sites"]] == EXPECTED_SITES


def test_declination_by_id(report):
    """Survey-grade declination against the current reference field."""
    got = report["declination_by_id"]
    assert isinstance(got, dict), "declination_by_id must be an object"
    bad = []
    for wid, exp in EXPECTED_DECLINATION.items():
        if wid not in got:
            bad.append("%s: missing" % wid)
            continue
        try:
            val = float(got[wid])
        except (TypeError, ValueError):
            bad.append("%s: non-numeric %r" % (wid, got[wid]))
            continue
        if abs(val - exp) > DECL_TOL:
            bad.append("%s: got %.4f, expected %.4f (d=%.4f)" % (wid, val, exp, val - exp))
            continue
        complaint = _rounding_complaint(wid, val, DECL_DECIMALS)
        if complaint:
            bad.append(complaint)
    assert not bad, ("%d of %d declinations are outside the %.2f deg survey tolerance:\n"
                     % (len(bad), len(EXPECTED_DECLINATION), DECL_TOL) + "\n".join(bad[:20]))


def test_true_bearing_by_id(report):
    """True bearings follow from the declinations, so they carry the same error."""
    got = report["true_bearing_by_id"]
    bad = []
    for wid, exp in EXPECTED_TRUE_BEARING.items():
        if wid not in got:
            bad.append("%s: missing" % wid)
            continue
        try:
            val = float(got[wid])
        except (TypeError, ValueError):
            bad.append("%s: non-numeric %r" % (wid, got[wid]))
            continue
        diff = abs((val - exp + 180.0) % 360.0 - 180.0)
        if diff > BEARING_TOL:
            bad.append("%s: got %.3f, expected %.3f" % (wid, val, exp))
            continue
        # The instruction requires the bearing normalised into [0, 360), which the
        # circular comparison above would otherwise let through as e.g. -17.0 for 343.0.
        if not (0.0 <= val < 360.0):
            bad.append("%s: %.3f is outside [0, 360)" % (wid, val))
            continue
        complaint = _rounding_complaint(wid, val, BEARING_DECIMALS)
        if complaint:
            bad.append(complaint)
    assert not bad, ("%d of %d true bearings are wrong:\n" % (len(bad), len(EXPECTED_TRUE_BEARING))
                     + "\n".join(bad[:20]))


def test_closure_km_by_site(report):
    """Track closure aggregates the whole reduced track."""
    got = report["closure_km_by_site"]
    bad = []
    for site, exp in EXPECTED_CLOSURE_KM.items():
        if site not in got:
            bad.append("%s: missing" % site)
            continue
        try:
            val = float(got[site])
        except (TypeError, ValueError):
            bad.append("%s: non-numeric %r" % (site, got[site]))
            continue
        if abs(val - exp) > CLOSURE_TOL:
            bad.append("%s: got %.3f km, expected %.3f km" % (site, val, exp))
            continue
        complaint = _rounding_complaint(site, val, DISTANCE_DECIMALS)
        if complaint:
            bad.append(complaint)
    assert not bad, "track closure wrong:\n" + "\n".join(bad)


# --- responsiveness probe -------------------------------------------------------
# Everything above reads one report produced from one archive, so a payload that was
# derived once and then written out verbatim is indistinguishable from a reduction that
# actually ran. This last check perturbs the archive by a known amount and re-runs the
# same entry point: a pipeline that computes tracks the change, a transcribed payload
# does not. It asserts only on report fields, so it holds whatever the internals look
# like.

PROBE_ID = "W001"
PROBE_DELTA_DEG = 10.0
WAYPOINTS_CSV = Path("/app/data/waypoints.csv")


def _bump_magnetic_bearing(text, waypoint_id, delta_deg):
    """Return the CSV with one waypoint's magnetic bearing advanced by delta_deg."""
    header, *rows = text.splitlines()
    col = header.split(",").index("magnetic_bearing_deg")
    out = [header]
    hits = 0
    for row in rows:
        if not row.strip():
            continue
        fields = row.split(",")
        if fields[0] == waypoint_id:
            fields[col] = "%.6g" % ((float(fields[col]) + delta_deg) % 360.0)
            hits += 1
        out.append(",".join(fields))
    assert hits == 1, "expected exactly one %s row, found %d" % (waypoint_id, hits)
    return "\n".join(out) + "\n"


def test_reduction_responds_to_the_archive(report):
    """The reduction must recompute from the feeds, not replay a fixed answer."""
    baseline_bearing = float(report["true_bearing_by_id"][PROBE_ID])
    baseline_decl = float(report["declination_by_id"][PROBE_ID])

    original = WAYPOINTS_CSV.read_text(encoding="utf-8")
    try:
        WAYPOINTS_CSV.write_text(
            _bump_magnetic_bearing(original, PROBE_ID, PROBE_DELTA_DEG),
            encoding="utf-8",
        )
        REPORT.unlink(missing_ok=True)
        proc = subprocess.run(
            [IMAGE_PYTHON, "-m", "navkit", "reduce"],
            cwd="/app", env=_image_env(), capture_output=True, text=True, timeout=600,
        )
        assert proc.returncode == 0, (
            "re-running the reduction on a perturbed archive exited %d\n"
            "--- stderr ---\n%s" % (proc.returncode, proc.stderr[-4000:])
        )
        assert REPORT.is_file(), "the re-run did not write /app/report.json"
        again = json.loads(REPORT.read_text(encoding="utf-8"))
    finally:
        WAYPOINTS_CSV.write_text(original, encoding="utf-8")

    moved = float(again["true_bearing_by_id"][PROBE_ID])
    shift = (moved - baseline_bearing) % 360.0
    assert abs(shift - PROBE_DELTA_DEG) <= BEARING_TOL, (
        "%s's magnetic bearing was advanced by %.1f degrees, so its true bearing should "
        "have moved by the same amount: it went %.3f -> %.3f (a shift of %.3f). A report "
        "that does not follow its own input has not been computed from it."
        % (PROBE_ID, PROBE_DELTA_DEG, baseline_bearing, moved, shift)
    )

    held = float(again["declination_by_id"][PROBE_ID])
    assert abs(held - baseline_decl) <= DECL_TOL, (
        "%s's declination depends on position, altitude and date, none of which changed, "
        "so it should have held at %.4f but became %.4f"
        % (PROBE_ID, baseline_decl, held)
    )
