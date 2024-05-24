import contextlib
from typing import Optional

import sqlalchemy as db
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import registry, relationship
from sqlalchemy.sql import func

from .models import TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace


def register_tables(engine: db.Engine) -> db.MetaData:
    metadata = db.MetaData()

    workspace = db.Table(
        "workspace",
        metadata,
        db.Column("created", db.DateTime(timezone=True), server_default=func.now()),
        db.Column("updated", db.DateTime(timezone=True), onupdate=func.now()),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
    )

    _map_imperatively(TogglWorkspace, workspace)

    client = db.Table(
        "client",
        metadata,
        db.Column("created", db.DateTime(timezone=True), server_default=func.now()),
        db.Column("updated", db.DateTime(timezone=True), onupdate=func.now()),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
    )
    _map_imperatively(TogglClient, client)

    project = db.Table(
        "project",
        metadata,
        db.Column("created", db.DateTime(timezone=True), server_default=func.now()),
        db.Column("updated", db.DateTime(timezone=True), onupdate=func.now()),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
        db.Column("color", db.String(6)),
        db.Column("client", db.ForeignKey("client.id")),
        db.Column("active", db.Boolean),
    )
    _map_imperatively(TogglProject, project)

    tag = db.Table(
        "tag",
        metadata,
        db.Column("created", db.DateTime(timezone=True), server_default=func.now()),
        db.Column("updated", db.DateTime(timezone=True), onupdate=func.now()),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.ForeignKey("workspace.id")),
    )
    _map_imperatively(TogglTag, tag)

    tracker = db.Table(
        "tracker",
        metadata,
        db.Column("created", db.DateTime(timezone=True), server_default=func.now()),
        db.Column("updated", db.DateTime(timezone=True), onupdate=func.now()),
        db.Column("id", db.Integer, primary_key=True, unique=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.ForeignKey("workspace.id")),
        db.Column("start", db.DateTime),
        db.Column("duration", db.Interval),
        db.Column("stop", db.DateTime),
        db.Column("project", db.ForeignKey("project.id")),
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
