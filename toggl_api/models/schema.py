# ruff: noqa: E402

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Optional

with contextlib.suppress(ImportError):
    import sqlalchemy as db
    from sqlalchemy.exc import ArgumentError
    from sqlalchemy.orm import registry, relationship
    from sqlalchemy.sql import func


from toggl_api.utility import requires

from .models import TogglClient, TogglOrganization, TogglProject, TogglTag, TogglTracker, TogglWorkspace

with contextlib.suppress(ImportError):
    from ._decorators import UTCDateTime


if TYPE_CHECKING:
    from sqlalchemy import MetaData, Table
    from sqlalchemy.engine import Engine


@requires("sqlalchemy")
def register_tables(engine: Engine) -> MetaData:
    metadata = db.MetaData()

    organization = db.Table(
        "organization",
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
    _map_imperatively(TogglOrganization, organization)

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
        db.Column("organization", db.Integer),
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


@requires("sqlalchemy")
def _map_imperatively(
    cls: type,
    table: Table,
    properties: Optional[dict] = None,
) -> None:
    mapper_registry = registry()
    properties = properties or {}
    with contextlib.suppress(ArgumentError):
        mapper_registry.map_imperatively(cls, table, properties=properties)
