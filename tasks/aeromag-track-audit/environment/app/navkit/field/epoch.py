"""Observation-date handling for field evaluation."""
import datetime

from ..errors import FieldError


def as_datetime(obs_date):
    """Turn an ISO ``YYYY-MM-DD`` observation date into a datetime for field evaluation."""
    raise NotImplementedError
