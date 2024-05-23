import sqlalchemy as db
from sqlalchemy.orm import registry, relationship

from .models import TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace

mapper_registry = registry()

metadata = db.MetaData()


workspace_table = db.Table(
    "workspace",
    metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("name", db.String(255)),
)

mapper_registry.map_imperatively(TogglWorkspace, workspace_table)

client_table = db.Table(
    "client",
    metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("name", db.String(255)),
    db.Column("workspace_id", db.Integer, db.ForeignKey("workspace.id")),
)

mapper_registry.map_imperatively(TogglClient, client_table)

project_table = db.Table(
    "project",
    metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("name", db.String(255)),
    db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
    db.Column("color", db.String(6)),
    db.Column("client", db.Integer, db.ForeignKey("client.id")),
    db.Column("active", db.Boolean),
)

mapper_registry.map_imperatively(TogglProject, project_table)

tag_table = db.Table(
    "tag",
    metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("name", db.String(255)),
    db.Column("workspace_id", db.Integer, db.ForeignKey("workspace.id")),
)


mapper_registry.map_imperatively(TogglTag, tag_table)

tracker_table = db.Table(
    "tracker",
    metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("description", db.String(255)),
    db.Column("workspace", db.Integer, db.ForeignKey("workspace.id")),
    db.Column("start", db.DateTime),
    db.Column("duration", db.Float),
    db.Column("stop", db.DateTime),
    db.Column("project", db.Integer, db.ForeignKey("project.id")),
)

mapper_registry.map_imperatively(
    TogglTracker,
    tracker_table,
    properties={"tags": relationship(TogglTag, "tracker")},
)
