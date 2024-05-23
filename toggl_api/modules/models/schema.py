import sqlalchemy as db
from sqlalchemy.orm import registry, relationship

from .models import TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace


def register_tables(engine: db.Engine) -> db.MetaData:
    metadata = db.MetaData()
    mapper_registry = registry()

    workspace = db.Table(
        "workspace",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
    )
    mapper_registry.map_imperatively(TogglWorkspace, workspace)

    client = db.Table(
        "client",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
    )
    mapper_registry.map_imperatively(TogglClient, client)

    project = db.Table(
        "project",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
        db.Column("color", db.String(6)),
        db.Column("client", db.Integer, db.ForeignKey("client.id")),
        db.Column("active", db.Boolean),
    )
    mapper_registry.map_imperatively(TogglProject, project)

    tag = db.Table(
        "tag",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
    )
    mapper_registry.map_imperatively(TogglTag, tag)

    tracker = db.Table(
        "tracker",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("name", db.String(255)),
        db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
        db.Column("start", db.DateTime),
        db.Column("duration", db.Float),
        db.Column("stop", db.DateTime),
        db.Column("project", db.Integer, db.ForeignKey("project.id")),
    )

    tracker_tag = db.Table(
        "tracker_tag",
        metadata,
        db.Column("tracker", db.ForeignKey("tracker.id")),
        db.Column("tag", db.ForeignKey("tag.id")),
    )
    mapper_registry.map_imperatively(
        TogglTracker,
        tracker,
        properties={"tags": relationship(TogglTag, secondary=tracker_tag)},
    )

    metadata.create_all(engine)

    return metadata
