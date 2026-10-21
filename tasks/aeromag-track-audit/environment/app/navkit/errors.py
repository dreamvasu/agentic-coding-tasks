"""Exception types raised across navkit."""


class NavkitError(Exception):
    """Base for every navkit failure."""


class ReaderError(NavkitError):
    """A survey feed could not be read."""


class GeometryError(NavkitError):
    """A coordinate or bearing was not well formed."""


class FieldError(NavkitError):
    """The geomagnetic field could not be evaluated."""
