from __future__ import annotations

import logging
import time
import warnings
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal, Optional, TypedDict

from toggl_api.meta.body import BaseBody
from toggl_api.meta.cache.base_cache import Comparison, TogglQuery
from toggl_api.meta.enums import RequestMethod

from .meta import TogglCachedEndpoint
from .models import TogglWorkspace

if TYPE_CHECKING:
    from datetime import datetime


log = logging.getLogger("toggl-api-wrapper.endpoint")


@dataclass
class WorkspaceBody(BaseBody):
    name: Optional[str] = field(default=None)
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

    rate_change_mode: Optional[Literal["start-today", "override-current", "override-all"]] = field(
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

    rounding: Optional[int] = field(
        default=None,
        metadata={
            "endpoints": frozenset(("add", "edit")),
        },
    )
    """Default rounding, premium feature, optional, only for existing WS"""

    rounding_minutes: Optional[int] = field(
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
            except ValueError as err:
                if str(err) != "No spaces allowed in the workspace name!":
                    raise
                log.warning(err)
                self.name = self.name.replace(" ", "-")
                log.warning("Updated to new name: %s!", self.name)

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Formats the body into a usable format for a request.

        Gets called form within an endpoint method.

        Args:
            endpoint: Which endpoint to target.
            body: Prefilled body with extra arguments.

        Returns:
            dict: A JSON body with the relevant parameters prefilled.
        """

        for fld in fields(self):
            if not self.verify_endpoint_parameter(fld.name, endpoint):
                continue

            value = getattr(self, fld.name)
            if not value:
                continue

            body[fld.name] = value

        return body


class WorkspaceEndpoint(TogglCachedEndpoint):
    """Specific endpoints for retrieving workspaces.

    [Official Documentation](https://engineering.toggl.com/docs/api/workspaces)
    """

    def get(
        self,
        workspace: Optional[TogglWorkspace | int] = None,
        *,
        refresh: bool = False,
    ) -> TogglWorkspace | None:
        """Get the current workspace based on the workspace_id class attribute.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#get-get-single-workspace)
        """
        if workspace is None:
            workspace = self.workspace_id
        elif isinstance(workspace, TogglWorkspace):
            workspace = workspace.id

        if not refresh:
            return self.cache.find_entry({"id": workspace})  # type: ignore[return-value]

        return self.request(f"workspaces/{workspace}", refresh=refresh)

    def add(self, body: WorkspaceBody) -> TogglWorkspace:
        """Create a new workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#post-create-a-new-workspace)

        Enterprise plan feature.

        Args:
            body: All settings for the workspace to be attached to as a body.

        Returns:
            TogglWorkspace: A newly created workspace with the supplied params.
        """
        return self.request(
            f"organizations/{self.organization_id}/workspaces",
            body=body.format("add", organization_id=self.organization_id),
            method=RequestMethod.POST,
            refresh=True,
        )

    def _collect_cache(self, since: int | None) -> list[TogglWorkspace]:
        if isinstance(since, int):
            ts = datetime.fromtimestamp(since, timezone.utc)
            cache = self.query(TogglQuery("timestamp", ts, Comparison.GREATER_THEN))
        else:
            cache = self.load_cache()

        return list(cache)

    def _validate_collect_since(self, since: datetime | int) -> int:
        since = since if isinstance(since, int) else int(time.mktime(since.timetuple()))
        now = int(time.mktime(datetime.now(tz=timezone.utc).timetuple()))
        if since > now:
            msg = "The 'since' argument needs to be before the current time!"
            raise ValueError(msg)
        return since

    def collect(
        self,
        since: Optional[datetime | int] = None,
        *,
        refresh: bool = False,
    ) -> list[TogglWorkspace]:
        """Lists workspaces for given user.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-workspaces)
        """

        if since is not None:
            since = self._validate_collect_since(since)

        if not refresh:
            return self._collect_cache(since)

        body = {"since": since} if since else None

        return self.request("me/workspaces", body=body, refresh=refresh)

    def edit(self, workspace_id: TogglWorkspace | int, body: WorkspaceBody) -> TogglWorkspace:
        """Update a specific workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#put-update-workspace)
        """
        if isinstance(workspace_id, TogglWorkspace):
            workspace_id = workspace_id.id

        return self.request(
            f"workspaces/{workspace_id}",
            body=body.format("edit"),
            method=RequestMethod.PUT,
            refresh=True,
        )

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return ""
