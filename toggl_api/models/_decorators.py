from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.types import DateTime, TypeDecorator


# NOTE: From sqlalchemy-utc package.
class UTCDateTime(TypeDecorator):
    """Almost equivalent to :class:`~sqlalchemy.types.DateTime` with
    ``timezone=True`` option, but it differs from that by:

    - Never silently take naive :class:`~datetime.datetime`, instead it
      always raise :exc:`ValueError` unless time zone aware value.
    - :class:`~datetime.datetime` value's :attr:`~datetime.datetime.tzinfo`
      is always converted to UTC.
    - Unlike SQLAlchemy's built-in :class:`~sqlalchemy.types.DateTime`,
      it never return naive :class:`~datetime.datetime`, but time zone
      aware value, even with SQLite or MySQL.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: datetime,
        _,
    ) -> datetime | None:
        if value is not None:
            if not isinstance(value, datetime):
                raise TypeError("Expected datetime.datetime, not " + repr(value))
            if value.tzinfo is None:
                msg = "Naive datetime is disallowed!"
                raise ValueError(msg)
            return value.astimezone(timezone.utc)
        return None

    def process_result_value(  # type: ignore[override]
        self,
        value: Optional[datetime],
        _,
    ) -> datetime | None:
        if value is not None:
            value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return value
