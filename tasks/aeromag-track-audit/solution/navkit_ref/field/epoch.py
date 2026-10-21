"""Observation-date handling for field evaluation."""
import datetime

from ..errors import FieldError


def as_datetime(obs_date):
    try:
        return datetime.datetime.fromisoformat(str(obs_date).strip())
    except ValueError as exc:
        raise FieldError("bad observation date %r" % obs_date) from exc
