"""Serialise the report."""
import json
import pathlib

from .. import config


def write_report(payload, path=None):
    """Write ``payload`` to the report path as a single JSON object."""
    raise NotImplementedError
