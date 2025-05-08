"""All endpoint functionality related modifiying and handling workspaces."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

from httpx import Client, HTTPStatusError, Response, Timeout, codes

from ._exceptions import DateTimeError, NamingError
from .meta import BaseBody, RequestMethod, TogglCachedEndpoint
from .meta.cache import Comparison, TogglCache, TogglQuery
from .models import TogglWorkspace
from .utility import get_timestamp

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api import TogglOrganization


log = logging.getLogger("toggl-api-wrapper.endpoint")


@dataclass
class WorkspaceBody(BaseBody):
    name: str | None = field(default=None)
    """Name of the workspace. Check TogglWorkspace static method for validation."""

    admins: list[int] = field(
        default_factory=list,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """List of admins, optional."""

    only_admins_may_create_projects: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Only admins will be able to create projects, optional,
    only for existing WS, will be false initially"""

    only_admins_may_create_tags: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Only admins will be able to create tags, optional,
    only for existing WS, will be false initially"""

    only_admins_see_billable_rates: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Whether only admins will be able to see billable rates, premium feature,
    optional, only for existing WS. Will be false initially"""

    only_admins_see_team_dashboard: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Only admins will be able to see the team dashboard, optional,
    only for existing WS, will be false initially"""

    projects_billable_by_default: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Whether projects will be set as billable by default, premium feature,
    optional, only for existing WS. Will be true initially"""

    projects_enforce_billable: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Whether tracking time to projects will enforce billable setting to be respected."""

    projects_private_by_default: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Whether projects will be set to private by default, optional.
    Will be true initially."""

    rate_change_mode: Literal["start-today", "override-current", "override-all"] | None = field(
        default=None,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """The rate change mode, premium feature, optional, only for existing WS.
    Can be 'start-today', 'override-current', 'override-all'"""

    reports_collapse: bool = field(
        default=False,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Whether reports should be collapsed by default, optional,
    only for existing WS, will be true initially"""

    rounding: int | None = field(
        default=None,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Default rounding, premium feature, optional, only for existing WS"""

    rounding_minutes: int | None = field(
        default=None,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Default rounding in minutes, premium feature, optional, only for existing WS"""

    def __post_init__(self) -> None:
        if self.name:
            try:
                TogglWorkspace.validate_name(self.name)
            except NamingError as err:
                if str(err) != "No spaces allowed in the workspace name!":
                    raise
                log.warning(err)
                self.name = self.name.replace(" ", "-")
                log.warning("Updated to new name: %s!", self.name)

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Format the body into a usable format for a request.

        Gets called form within an endpoint method.

        Args:
            endpoint: Which endpoint to target.
            body: Prefilled body with extra arguments.

        Returns:
            A JSON body with the relevant parameters prefilled.
        """
        for fld in fields(self):
            if not self._verify_endpoint_parameter(fld.name, endpoint):
                continue

            value = getattr(self, fld.name)
            if not value:
                continue

            body[fld.name] = value

        return body


class User(TypedDict):
    user_id: int
    name: str


class WorkspaceStatistics(TypedDict):
    admins: list[User]
    groups_count: int
    members_count: int


class WorkspaceEndpoint(TogglCachedEndpoint[TogglWorkspace]):
    """Specific endpoints for retrieving and modifying workspaces.

    [Official Documentation](https://engineering.toggl.com/docs/api/workspaces)

    Examples:
        >>> org_id = 123213324
        >>> workspace_endpoint = WorkspaceEndpoint(org_id, BasicAuth(...), SqliteCache(...))

    Params:
        organization_id: Workspace endpoint takes an organization id instead of
            a workspace id.
        auth: Authentication for the client.
        cache: Cache object for caching toggl workspace data to disk. Builtin cache
            types are JSONCache and SqliteCache.
        client: Optional client to be passed to be used for requests. Useful
            when a global client is used and needs to be recycled.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    MODEL = TogglWorkspace

    def __init__(
        self,
        organization_id: int | TogglOrganization,
        auth: BasicAuth,
        cache: TogglCache[TogglWorkspace] | None = None,
        *,
        client: Client | None = None,
        timeout: Timeout | int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(
            auth,
            cache,
            client=client,
            timeout=timeout,
            re_raise=re_raise,
            retries=retries,
        )
        self.organization_id = organization_id if isinstance(organization_id, int) else organization_id.id

    def get(
        self,
        workspace: TogglWorkspace | int,
        *,
        refresh: bool = False,
    ) -> TogglWorkspace | None:
        """Get the current workspace based on an id or model.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#get-get-single-workspace)

        Args:
            workspace: Workspace id or model.
            refresh: Whether to use cache or not.

        Raises:
            HTTPStatusError: If anything that's not a '2xx' or '404' status_code is returned.

        Returns:
            Model of workspace if found else none.
        """
        if isinstance(workspace, TogglWorkspace):
            workspace = workspace.id

        if self.cache and not refresh:
            return self.cache.find({"id": workspace})

        try:
            response = self.request(f"workspaces/{workspace}", refresh=refresh)
        except HTTPStatusError as err:
            log.exception("%s")
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                return None
            raise

        return cast("TogglWorkspace", response)

    def add(self, body: WorkspaceBody) -> TogglWorkspace:
        """Create a new workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#post-create-a-new-workspace)

        Enterprise plan feature.

        Args:
            body: All settings for the workspace to be attached to as a body.

        Returns:
            A newly created workspace with the supplied params.
        """
        return cast(
            "TogglWorkspace",
            self.request(
                f"organizations/{self.organization_id}/workspaces",
                body=body.format("add", organization_id=self.organization_id),
                method=RequestMethod.POST,
                refresh=True,
            ),
        )

    def _collect_cache(self, since: int | None) -> list[TogglWorkspace]:
        if isinstance(since, int):
            ts = datetime.fromtimestamp(since, timezone.utc)
            return list(self.query(TogglQuery("timestamp", ts, Comparison.GREATER_THEN)))
        return list(self.load_cache())

    def _validate_collect_since(self, since: datetime | int) -> int:
        since = get_timestamp(since)
        now = int(time.mktime(datetime.now(tz=timezone.utc).timetuple()))
        if since > now:
            msg = "The 'since' argument needs to be before the current time!"
            raise DateTimeError(msg)
        return since

    def collect(
        self,
        since: datetime | int | None = None,
        *,
        refresh: bool = False,
    ) -> list[TogglWorkspace]:
        """List workspaces for given user.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-workspaces)

        Args:
            since: Optional argument to filter any workspace after the timestamp.
            refresh: Whether to use cache or not.

        Raises:
            DateTimeError: If the since argument is after the current time.

        Returns:
            A list of workspaces or empty if there are None assocciated with the user.
        """
        if since is not None:
            since = self._validate_collect_since(since)

        if self.cache and not refresh:
            return self._collect_cache(since)

        body = {"since": since} if since else None

        return cast(
            "list[TogglWorkspace]",
            self.request("me/workspaces", body=body, refresh=refresh),
        )

    def edit(self, workspace_id: TogglWorkspace | int, body: WorkspaceBody) -> TogglWorkspace:
        """Update a specific workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#put-update-workspace)

        Raises:
            HTTPStatusError: For anything thats not an *ok* status code.

        Returns:
            A workspace model with the supplied edits.
        """
        if isinstance(workspace_id, TogglWorkspace):
            workspace_id = workspace_id.id

        return cast(
            "TogglWorkspace",
            self.request(
                f"workspaces/{workspace_id}",
                body=body.format("edit"),
                method=RequestMethod.PUT,
                refresh=True,
            ),
        )

    def tracker_constraints(self, workspace_id: TogglWorkspace | int) -> dict[str, bool]:
        """Get the time entry constraints for a given workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#get-get-workspace-time-entry-constraints)

        Toggl premium feature.

        Examples:
            >>> workspace_endpoint.get_workspace_constraints(24214214)
            {
                "description_present": True,
                "project_present": False,
                "tag_present": False",
                "task_present": False,
                "time_entry_constraints_enabled": True,
            }

        Args:
            workspace_id: Id of the workspace to retrieve constraints from.

        Returns:
            A dictionary of booleans containing the settings.
        """
        if isinstance(workspace_id, TogglWorkspace):
            workspace_id = workspace_id.id

        return cast(
            "dict[str, bool]",
            cast(
                "Response",
                self.request(
                    f"workspaces/{workspace_id}/time_entry_constraints",
                    raw=True,
                    refresh=True,
                ),
            ).json(),
        )

    def statistics(self, workspace_id: TogglWorkspace | int) -> WorkspaceStatistics:
        """Return workspace admins list, members count and groups count.

        [Official Documentation](https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/statistics)

        Args:
            workspace_id: Id of the workspace to fetch the statistics from.

        Returns:
            A dictionary containing relevant statistics.
                Refer to WorkspaceStatistics typed dict for reference.
        """
        if isinstance(workspace_id, TogglWorkspace):
            workspace_id = workspace_id.id

        return cast(
            "WorkspaceStatistics",
            cast(
                "Response",
                self.request(
                    f"workspaces/{workspace_id}/statistics",
                    refresh=True,
                    raw=True,
                ),
            ).json(),
        )
