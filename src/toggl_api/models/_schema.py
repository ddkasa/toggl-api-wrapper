# ruff: noqa: E402

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

with contextlib.suppress(ImportError):
    from sqlalchemy import (
        Boolean,
        Column,
        Date,
        ForeignKey,
        Integer,
        Interval,
        MetaData,
        String,
        Table,
    )
    from sqlalchemy.exc import ArgumentError
    from sqlalchemy.orm import registry, relationship
    from sqlalchemy.sql import func


from toggl_api._utility import _requires

from ._models import (
    TogglClient,
    TogglOrganization,
    TogglProject,
    TogglTag,
    TogglTracker,
    TogglWorkspace,
)

with contextlib.suppress(ImportError):
    from ._decorators import UTCDateTime


if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


@_requires("sqlalchemy")
def _create_mappings(metadata: MetaData) -> None:
    organization = Table(
        "organization",
        metadata,
        Column(
            "created",
            UTCDateTime(timezone=True),
            server_default=func.now(),
        ),
        Column("timestamp", UTCDateTime(timezone=True)),
        Column("id", Integer, primary_key=True),
        Column("name", String(255)),
    )
    _map_imperatively(TogglOrganization, metadata, organization)

    workspace = Table(
        "workspace",
        metadata,
        Column(
            "created",
            UTCDateTime(timezone=True),
            server_default=func.now(),
        ),
        Column("timestamp", UTCDateTime(timezone=True)),
        Column("id", Integer, primary_key=True),
        Column("name", String(255)),
        Column("organization", Integer),
    )

    _map_imperatively(TogglWorkspace, metadata, workspace)

    client = Table(
        "client",
        metadata,
        Column(
            "created",
            UTCDateTime(timezone=True),
            server_default=func.now(),
        ),
        Column("timestamp", UTCDateTime),
        Column("id", Integer, primary_key=True),
        Column("name", String(255)),
        Column("workspace", Integer, ForeignKey("workspace.id")),
    )
    _map_imperatively(TogglClient, metadata, client)

    project = Table(
        "project",
        metadata,
        Column("created", UTCDateTime, server_default=func.now()),
        Column("timestamp", UTCDateTime),
        Column("id", Integer, primary_key=True),
        Column("name", String(255)),
        Column("workspace", Integer, ForeignKey("workspace.id")),
        Column("color", String(6)),
        Column("client", Integer, ForeignKey("client.id")),
        Column("active", Boolean),
        Column("start_date", Date),
        Column("stop_date", Date),
    )
    _map_imperatively(TogglProject, metadata, project)

    tag = Table(
        "tag",
        metadata,
        Column("created", UTCDateTime, server_default=func.now()),
        Column("timestamp", UTCDateTime),
        Column("id", Integer, primary_key=True),
        Column("name", String(255)),
        Column("workspace", Integer, ForeignKey("workspace.id")),
    )
    _map_imperatively(TogglTag, metadata, tag)

    tracker = Table(
        "tracker",
        metadata,
        Column("created", UTCDateTime, server_default=func.now()),
        Column("timestamp", UTCDateTime),
        Column("id", Integer, primary_key=True),
        Column("name", String(255)),
        Column("workspace", Integer, ForeignKey("workspace.id")),
        Column("start", UTCDateTime),
        Column("duration", Interval, nullable=True),
        Column("stop", UTCDateTime, nullable=True),
        Column("project", Integer, ForeignKey("project.id"), nullable=True),
    )

    tracker_tag = Table(
        "tracker_tag",
        metadata,
        Column("tracker", ForeignKey("tracker.id")),
        Column("tag", ForeignKey("tag.id")),
    )
    _map_imperatively(
        TogglTracker,
        metadata,
        tracker,
        properties={"tags": relationship(TogglTag, secondary=tracker_tag)},
    )


@_requires("sqlalchemy")
def register_tables(engine: Engine) -> MetaData:
    metadata = MetaData()

    _create_mappings(metadata)

    metadata.create_all(engine)

    return metadata


@_requires("sqlalchemy")
def _map_imperatively(
    cls: type,
    metadata: MetaData,
    table: Table,
    properties: dict[str, Any] | None = None,
) -> None:
    mapper_registry = registry(metadata=metadata)
    properties = properties or {}
    with contextlib.suppress(ArgumentError):
        mapper_registry.map_imperatively(cls, table, properties=properties)
