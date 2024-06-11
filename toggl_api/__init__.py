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
    "ClientBody",
    "ClientEndpoint",
    "JSONCache",
    "ProjectBody",
    "ProjectEndpoint",
    "SqliteCache",
    "TagEndpoint",
    "TogglClient",
    "TogglProject",
    "TogglTag",
    "TogglTracker",
    "TogglWorkspace",
    "TrackerBody",
    "TrackerEndpoint",
    "UserEndpoint",
    "UserEndpoint",
    "WorkspaceEndpoint",
    "generate_authentication",
]
