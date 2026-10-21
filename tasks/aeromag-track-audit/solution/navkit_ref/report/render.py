"""Serialise the report."""
import json
import pathlib

from .. import config


def write_report(payload, path=None):
    p = pathlib.Path(path or config.REPORT_PATH)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return p
