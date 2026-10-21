"""
Grades the recovered payloads against the true current value of each target key.
Only the SHA-256 digests are stored in expected_hashes.json, never the payloads.
"""

import hashlib
import json
from pathlib import Path

import pytest

IDS = ["0007", "0019", "0042", "0063", "0104", "0137",
       "0205", "0268", "0301", "0358", "0412", "0470"]

EXPECTED = json.loads((Path(__file__).parent / "expected_hashes.json").read_text())
OUTPUT = Path("/app/output")


@pytest.mark.parametrize("doc_id", IDS)
def test_recovered_payload_matches_current(doc_id):
    """/app/output/<id>.bin exists and its SHA-256 equals that key's current payload."""
    expected = EXPECTED[f"obj:{doc_id}"]
    path = OUTPUT / f"{doc_id}.bin"
    assert path.is_file(), f"missing recovered payload: {path}"
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    assert got == expected, (
        f"id {doc_id}: SHA-256 mismatch\n  expected {expected}\n  got      {got}"
    )
