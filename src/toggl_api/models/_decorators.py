from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.types import DateTime, TypeDecorator

if TYPE_CHECKING:
    from sqlalchemy import Dialect


# NOTE: From sqlalchemy-utc package.
class UTCDateTime(TypeDecorator[datetime]):
    """Equivalent to `sqlalchemy.types.DateTime` with UTC timezone.

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

    def process_bind_param(
        self,
        value: datetime | None,
        _dialect: Dialect,
    ) -> datetime | None:
        if value is not None:
            if not isinstance(value, datetime):
                raise TypeError(
                    "Expected datetime.datetime, not " + repr(value),
                )
            if value.tzinfo is None:
                msg = "Naive datetime is disallowed!"
                raise ValueError(msg)
            return value.astimezone(timezone.utc)
        return None

    def process_result_value(
        self,
        value: datetime | None,
        _dialect: Dialect,
    ) -> datetime | None:
        if value is not None:
            value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return value
