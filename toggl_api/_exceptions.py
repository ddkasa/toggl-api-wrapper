from __future__ import annotations


class NamingError(ValueError):
    """Description or name is invalid."""


class DateTimeError(ValueError):
    """Datetime is invalid or out of range."""


class MissingParentError(AttributeError):
    """Cache object doesn't have a parent endpoint associated and is being called used."""


class NoCacheAssignedError(AttributeError):
    """Endpoint doesn't have cache object associated with it and try's to manipulate cache."""
