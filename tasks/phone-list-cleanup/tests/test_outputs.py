"""Verifier for the phone-list audit at /app/report.json.

Checks the five required fields against the reference computed from CURRENT
numbering-plan metadata (phonenumbers 9.0.34). Under the image's pinned, stale
8.13.52 the row count still reconciles (total_numbers) while valid_count,
invalid_ids, type_histogram, and carrier_by_id come out silently wrong for the
regions whose plans changed in 2023-2025. Only the produced output file is
inspected. Standard library only.
"""
import json
from pathlib import Path

import pytest

REPORT = Path("/app/report.json")

EXPECTED_TOTAL = 42
EXPECTED_VALID = 36
EXPECTED_INVALID = ["c02", "c06", "c18", "c22", "c34", "c37"]
EXPECTED_TYPES = {"FIXED_LINE": 8, "FIXED_LINE_OR_MOBILE": 6, "MOBILE": 22}
EXPECTED_CARRIERS = {
    "c01": "Idea", "c05": "T-Mobile", "c07": "JT", "c08": "", "c09": "TIM",
    "c11": "KDDI", "c12": "at", "c13": "SFR", "c14": "Digicel", "c17": "Optus",
    "c19": "Syma", "c21": "TIM", "c23": "SingTel", "c24": "Unitel", "c25": "KPN",
    "c28": "at", "c29": "Vodacom", "c30": "Digicel", "c33": "MTN",
    "c38": "Lao Telecom", "c40": "at", "c41": "Digicel",
}


@pytest.fixture(scope="module")
def report():
    """/app/report.json exists and is a single JSON object (instruction: 'Write
    only the JSON object to /app/report.json')."""
    assert REPORT.exists(), "/app/report.json does not exist"
    try:
        data = json.loads(REPORT.read_text(encoding="utf-8"))
    except Exception as e:
        pytest.fail(f"/app/report.json is not valid JSON: {e}")
    assert isinstance(data, dict), f"report.json must be a JSON object, got {type(data).__name__}"
    return data


def test_total_numbers(report):
    """`total_numbers` is the row count (reconciles regardless of metadata)."""
    assert "total_numbers" in report, "missing field 'total_numbers'"
    assert int(str(report["total_numbers"]).strip()) == EXPECTED_TOTAL, (
        f"total_numbers: got {report['total_numbers']!r}, expected {EXPECTED_TOTAL}"
    )


def test_valid_count(report):
    """`valid_count` reflects current numbering plans; the stale library over- or
    under-counts validity for the changed regions (Benin/Saudi drop, Chile adds)."""
    assert "valid_count" in report, "missing field 'valid_count'"
    assert int(str(report["valid_count"]).strip()) == EXPECTED_VALID, (
        f"valid_count: got {report['valid_count']!r}, expected {EXPECTED_VALID}"
    )


def test_invalid_ids(report):
    """`invalid_ids` is the sorted set of ids whose number is not valid today."""
    assert "invalid_ids" in report, "missing field 'invalid_ids'"
    got = report["invalid_ids"]
    assert isinstance(got, list), f"invalid_ids must be a list, got {type(got).__name__}"
    assert [str(x) for x in got] == EXPECTED_INVALID, (
        f"invalid_ids: got {got!r}, expected {EXPECTED_INVALID}"
    )


def test_type_histogram(report):
    """`type_histogram` counts valid numbers by line type; type reclassifications
    (e.g. Laos UAN->MOBILE, US VOIP->FIXED_LINE_OR_MOBILE) shift the counts."""
    assert "type_histogram" in report, "missing field 'type_histogram'"
    got = report["type_histogram"]
    assert isinstance(got, dict), f"type_histogram must be an object, got {type(got).__name__}"
    try:
        got_norm = {str(k): int(v) for k, v in got.items()}
    except Exception as e:
        pytest.fail(f"type_histogram has a non-integer value: {e}")
    assert got_norm == EXPECTED_TYPES, (
        f"type_histogram: got {got_norm}, expected {EXPECTED_TYPES}"
    )


def test_carrier_by_id(report):
    """`carrier_by_id` maps each valid MOBILE id to its allocated network; carrier
    metadata changes (Ghana 'airteltiGO'->'at', Trinidad 'bmobile'->'Digicel')
    and the Laos type flip change which ids appear and their values."""
    assert "carrier_by_id" in report, "missing field 'carrier_by_id'"
    got = report["carrier_by_id"]
    assert isinstance(got, dict), f"carrier_by_id must be an object, got {type(got).__name__}"
    got_norm = {str(k): ("" if v is None else str(v)) for k, v in got.items()}
    assert got_norm == EXPECTED_CARRIERS, (
        f"carrier_by_id mismatch. "
        f"missing_or_wrong={{k: EXPECTED_CARRIERS[k] for k in EXPECTED_CARRIERS if got_norm.get(k) != EXPECTED_CARRIERS[k]}}, "
        f"extra={{k: got_norm[k] for k in got_norm if k not in EXPECTED_CARRIERS}}"
    )
