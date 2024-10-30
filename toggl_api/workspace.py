from __future__ import annotations

import logging
import time
import warnings
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal, Optional, TypedDict

from toggl_api.meta.body import BaseBody
from toggl_api.meta.enums import RequestMethod

from .meta import TogglCachedEndpoint
from .models import TogglWorkspace


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

        return self.request(f"{workspace}", refresh=refresh)

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return "workspaces/"
