from __future__ import annotations


class NamingError(ValueError):
    """Raised when a description or name is invalid."""


class DateTimeError(ValueError):
    """Raised when a date is invalid or out of range."""
