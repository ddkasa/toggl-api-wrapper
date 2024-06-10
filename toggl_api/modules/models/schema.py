import contextlib
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as db
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import registry, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime, TypeDecorator

from .models import TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace


# TODO: From sqlalchemy-utc package. Should look for better solution.
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
    ) -> Optional[datetime]:
        if value is not None:
            if not isinstance(value, datetime):
                raise TypeError("expected datetime.datetime, not " + repr(value))
            if value.tzinfo is None:
                msg = "naive datetime is disallowed"
                raise ValueError(msg)
            return value.astimezone(timezone.utc)
        return None

    def process_result_value(  # type: ignore[override]
        self,
        value: Optional[datetime],
        _,
    ) -> Optional[datetime]:
        if value is not None:
            value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return value


def register_tables(engine: Engine) -> db.MetaData:
    metadata = db.MetaData()

    workspace = db.Table(
        "workspace",
        metadata,
        db.Column(
            "created",
            UTCDateTime(timezone=True),
            server_default=func.now(),
        ),
        db.Column("timestamp", UTCDateTime(timezone=True)),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
    )

    _map_imperatively(TogglWorkspace, workspace)

    client = db.Table(
        "client",
        metadata,
        db.Column("created", UTCDateTime(timezone=True), server_default=func.now()),
        db.Column("timestamp", UTCDateTime),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
    )
    _map_imperatively(TogglClient, client)

    project = db.Table(
        "project",
        metadata,
        db.Column("created", UTCDateTime, server_default=func.now()),
        db.Column("timestamp", UTCDateTime),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
        db.Column("color", db.String(6)),
        db.Column("client", db.Integer, db.ForeignKey("client.id")),
        db.Column("active", db.Boolean),
    )
    _map_imperatively(TogglProject, project)

    tag = db.Table(
        "tag",
        metadata,
        db.Column("created", UTCDateTime, server_default=func.now()),
        db.Column("timestamp", UTCDateTime),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
    )
    _map_imperatively(TogglTag, tag)

    tracker = db.Table(
        "tracker",
        metadata,
        db.Column("created", UTCDateTime, server_default=func.now()),
        db.Column("timestamp", UTCDateTime),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
        db.Column("start", UTCDateTime),
        db.Column("duration", db.Interval, nullable=True),
        db.Column("stop", UTCDateTime, nullable=True),
        db.Column("project", db.Integer, db.ForeignKey("project.id"), nullable=True),
    )

    tracker_tag = db.Table(
        "tracker_tag",
        metadata,
        db.Column("tracker", db.ForeignKey("tracker.id")),
        db.Column("tag", db.ForeignKey("tag.id")),
    )
    _map_imperatively(
        TogglTracker,
        tracker,
        properties={"tags": relationship(TogglTag, secondary=tracker_tag)},
    )

    metadata.create_all(engine)

    return metadata


def _map_imperatively(
    cls: type,
    table: db.Table,
    properties: Optional[dict] = None,
) -> None:
    mapper_registry = registry()
    properties = {} if properties is None else properties
    with contextlib.suppress(ArgumentError):
        mapper_registry.map_imperatively(cls, table, properties=properties)
