from .config import generate_authentication
from .modules import (
    ClientBody,
    ClientEndpoint,
    JSONCache,
    ProjectBody,
    ProjectEndpoint,
    SqliteCache,
    TagEndpoint,
    TrackerBody,
    TrackerEndpoint,
    UserEndpoint,
    WorkspaceEndpoint,
)
from .modules.models import (
    TogglClient,
    TogglProject,
    TogglTag,
    TogglTracker,
    TogglWorkspace,
)
from .version import version

__author__ = "David Kasakaitis"
__version__ = version


__all__ = [
    "TogglClient",
    "TogglProject",
    "TogglTag",
    "TogglTracker",
    "TogglWorkspace",
    "ClientEndpoint",
    "TagEndpoint",
    "UserEndpoint",
    "WorkspaceEndpoint",
    "ProjectEndpoint",
    "TrackerEndpoint",
    "UserEndpoint",
    "TrackerBody",
    "ProjectBody",
    "ClientBody",
    "generate_authentication",
    "SqliteCache",
    "JSONCache",
]
