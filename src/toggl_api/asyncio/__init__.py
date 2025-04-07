"""All methods for concurrent programming."""

from importlib.util import find_spec

if not find_spec("sqlalchemy"):
    msg = "SQLAlchemy is required for the async module!"
    raise SystemExit(msg)

if not find_spec("greenlet"):
    msg = "Greenlet is required for the async module!"
    raise SystemExit(msg)


from ._async_cache import TogglAsyncCache
from ._async_client import AsyncClientEndpoint
from ._async_endpoint import TogglAsyncCachedEndpoint, TogglAsyncEndpoint
from ._async_organization import AsyncOrganizationEndpoint
from ._async_project import AsyncProjectEndpoint
from ._async_reports import (
    AsyncDetailedReportEndpoint,
    AsyncReportEndpoint,
    AsyncSummaryReportEndpoint,
    AsyncWeeklyReportEndpoint,
)
from ._async_sqlite_cache import AsyncSqliteCache, async_register_tables
from ._async_tag import AsyncTagEndpoint
from ._async_tracker import AsyncTrackerEndpoint
from ._async_user import AsyncUserEndpoint
from ._async_workspace import AsyncWorkspaceEndpoint

__all__ = (
    "AsyncClientEndpoint",
    "AsyncDetailedReportEndpoint",
    "AsyncOrganizationEndpoint",
    "AsyncProjectEndpoint",
    "AsyncReportEndpoint",
    "AsyncSqliteCache",
    "AsyncSummaryReportEndpoint",
    "AsyncTagEndpoint",
    "AsyncTrackerEndpoint",
    "AsyncUserEndpoint",
    "AsyncWeeklyReportEndpoint",
    "AsyncWorkspaceEndpoint",
    "TogglAsyncCache",
    "TogglAsyncCachedEndpoint",
    "TogglAsyncEndpoint",
    "async_register_tables",
)
