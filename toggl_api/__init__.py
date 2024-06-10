from .modules import (
    ClientEndpoint,
    ProjectBody,
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
    "TrackerEndpoint",
    "UserEndpoint",
    "TrackerBody",
    "ProjectBody",
]
