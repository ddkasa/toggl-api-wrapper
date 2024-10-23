from .client import ClientBody, ClientEndpoint
from .config import generate_authentication
from .meta import JSONCache
from .meta.cache import Comparison, TogglQuery
from .models import (
    TogglClient,
    TogglProject,
    TogglSubscription,
    TogglTag,
    TogglTracker,
    TogglWorkspace,
)
from .project import ProjectBody, ProjectEndpoint
from .tag import TagEndpoint
from .tracker import TrackerBody, TrackerEndpoint
from .user import UserEndpoint
from .version import version
from .webhooks import SubscriptionEndpoint, WebhookBody, WebhookEndpoint
from .workspace import WorkspaceEndpoint

__author__ = "David Kasakaitis"
__version__ = version
__typed__ = True


__all__ = [
    "ClientBody",
    "ClientEndpoint",
    "Comparison",
    "JSONCache",
    "ProjectBody",
    "ProjectEndpoint",
    "SubscriptionEndpoint",
    "TagEndpoint",
    "TogglClient",
    "TogglProject",
    "TogglQuery",
    "TogglSubscription",
    "TogglTag",
    "TogglTracker",
    "TogglWorkspace",
    "TrackerBody",
    "TrackerEndpoint",
    "UserEndpoint",
    "UserEndpoint",
    "WebhookBody",
    "WebhookEndpoint",
    "WorkspaceEndpoint",
    "generate_authentication",
]
