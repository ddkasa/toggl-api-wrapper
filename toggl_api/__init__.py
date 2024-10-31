from .client import ClientBody, ClientEndpoint
from .config import generate_authentication
from .meta import JSONCache
from .meta.cache import Comparison, TogglQuery
from .models import TogglClient, TogglOrganization, TogglProject, TogglTag, TogglTracker, TogglWorkspace
from .organization import OrganizationEndpoint
from .project import ProjectBody, ProjectEndpoint
from .tag import TagEndpoint
from .tracker import TrackerBody, TrackerEndpoint
from .user import UserEndpoint
from .version import version
from .workspace import WorkspaceBody, WorkspaceEndpoint

__author__ = "David Kasakaitis"
__version__ = version
__typed__ = True


__all__ = (  # noqa: RUF022
    "ClientBody",
    "ClientEndpoint",
    "Comparison",
    "JSONCache",
    "ProjectBody",
    "ProjectEndpoint",
    "TagEndpoint",
    "TogglClient",
    "TogglProject",
    "TogglQuery",
    "TogglTag",
    "TogglTracker",
    "TogglWorkspace",
    "TrackerBody",
    "TrackerEndpoint",
    "UserEndpoint",
    "UserEndpoint",
    "WorkspaceBody",
    "WorkspaceEndpoint",
    "generate_authentication",
    "TogglOrganization",
    "OrganizationEndpoint",
)
