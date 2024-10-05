import warnings

from .client import ClientBody, ClientEndpoint
from .meta import JSONCache, SqliteCache
from .project import ProjectBody, ProjectEndpoint
from .tag import TagEndpoint
from .tracker import TrackerBody, TrackerEndpoint
from .user import UserEndpoint
from .workspace import WorkspaceEndpoint

warnings.warn(
    "The 'modules' namespace will be merged with the 'toggl_api' namespace in v1.0.0",
    DeprecationWarning,
    stacklevel=2,
)
__all__ = (
    "ClientBody",
    "ClientEndpoint",
    "JSONCache",
    "ProjectBody",
    "ProjectEndpoint",
    "SqliteCache",
    "TagEndpoint",
    "TrackerBody",
    "TrackerEndpoint",
    "UserEndpoint",
    "WorkspaceEndpoint",
)
