from datetime import datetime
from typing import Final

ISO_FORMAT: Final[str] = r"%Y-%m-%dT%H:%M:%S"

# NOTE: Date utilities for python 3.10 compatibility.


def format_iso(date: datetime) -> str:
    return date.isoformat(timespec="seconds")


def parse_iso(date: str) -> datetime:
    if date.endswith("Z"):
        date = date[:-1] + "-00:00"
    return datetime.fromisoformat(date)
