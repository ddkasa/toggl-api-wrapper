from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final, Literal, Optional

from httpx import HTTPStatusError, codes

from toggl_api._exceptions import NamingError
from toggl_api.utility import format_iso

from .meta import BaseBody, RequestMethod, TogglCachedEndpoint
from .models import TogglProject

if TYPE_CHECKING:
    from datetime import date

    from httpx import BasicAuth

    from toggl_api.meta import TogglCache

    from .models import TogglWorkspace

log = logging.getLogger("toggl-api-wrapper.endpoint")


@dataclass
class ProjectBody(BaseBody):
    """JSON body dataclass for PUT, POST & PATCH requests."""

    name: Optional[str] = field(default=None)
    """Name of the project. Defaults to None. Will be required if its a POST request."""

    active: bool | Literal["both"] = field(default="both")
    """Whether the project is archived or active.
    The literal 'both' is used for querying."""
    is_private: Optional[bool] = field(
        default=True,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Whether the project is private or not. Defaults to True."""

    client_id: Optional[int] = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    client_name: Optional[str] = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Client name if client_id is not set. Defaults to None. If client_id is
    set the client_name will be ignored."""

    color: Optional[str] = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )

    start_date: Optional[date] = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Date to set the start of a project. If not set or start date is after
    the end date the end date will be ignored."""

    end_date: Optional[date] = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Date to set the end of the project. If not set or start date is after
    the end date the end date will be ignored."""

    since: Optional[date | int] = field(
        default=None,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Timestamp for querying for projects with the 'collect' endpoint.
    Retrieve projects created/modified/deleted since this date using UNIX timestamp.
    *If using local cache deleted projects are not present.*
    """

    user_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific projects with assocciated users. API only."""

    client_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific projects with assocciated clients."""

    group_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific projects with assocciated groups. API only"""

    statuses: list[TogglProject.Status] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific statuses when using the collect endpoint.
    Deleted status only works with the remote API.
    """

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Formats the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            endpoint: Name of the endpoint for filtering purposes.
            body: Additional arguments for the body.

        Returns:
            dict[str, Any]: JSON compatible formatted body.
        """
        body.update(
            {
                "active": self.active,
                "is_private": self.is_private,
            },
        )

        if self.client_id:
            body["client_id"] = self.client_id
        elif self.client_name:
            body["client_name"] = self.client_name

        if self.color:
            color = ProjectEndpoint.get_color(self.color) if self.color in ProjectEndpoint.BASIC_COLORS else self.color
            body["color"] = color

        if self.start_date:
            body["start_date"] = format_iso(self.start_date)
            if self.end_date and self.end_date > self.start_date:
                body["end_date"] = format_iso(self.end_date)

        if self.name:
            body["name"] = self.name

        return body


class ProjectEndpoint(TogglCachedEndpoint[TogglProject]):
    """Specific endpoints for retrieving and modifying projects.

    [Official Documentation](https://engineering.toggl.com/docs/api/projects)

    Params:
        workspace_id: The workspace the projects belong to.
    """

    BASIC_COLORS: Final[dict[str, str]] = {
        "blue": "#0b83d9",
        "violet": "#9e5bd9",
        "pink": "#d94182",
        "orange": "#e36a00",
        "gold": "#bf7000",
        "green": "#2da608",
        "teal": "#06a893",
        "beige": "#c9806b",
        "dark-blue": "#465bb3",
        "purple": "#990099",
        "yellow": "#c7af14",
        "dark-green": "#566614",
        "red": "#d92b2b",
        "gray": "#525266",
    }
    """Basic colors available for projects in order."""

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: TogglCache[TogglProject],
        *,
        timeout: int = 20,
        **kwargs: Any,
    ) -> None:
        super().__init__(0, auth, cache, timeout=timeout, **kwargs)
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    def collect(self, *, refresh: bool = False) -> list[TogglProject]:
        """Returns all cached or remote projects.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#get-workspaceprojects)
        """
        return self.request("", refresh=refresh)

    def get(self, project_id: int | TogglProject, *, refresh: bool = False) -> TogglProject | None:
        """Request a projects based on its id.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#get-workspaceproject)
        """
        if isinstance(project_id, TogglProject):
            project_id = project_id.id

        if not refresh:
            return self.cache.find_entry({"id": project_id})  # type: ignore[return-value]

        try:
            response = self.request(
                f"/{project_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if err.response.status_code == codes.NOT_FOUND:
                log.warning("Project with id %s was not found!", project_id)
                return None
            raise

        return response or None

    def delete(self, project: TogglProject | int) -> None:
        """Deletes a project based on its id.

        This endpoint always hit the external API in order to keep projects consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#delete-workspaceproject)
        """

        project_id = project if isinstance(project, int) else project.id
        try:
            self.request(
                f"/{project_id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != codes.NOT_FOUND:
                raise
            log.warning(
                "Project with id %s was either already deleted or did not exist in the first place!",
                project_id,
            )

        if isinstance(project, int):
            proj = self.cache.find_entry({"id": project})
            if not isinstance(proj, TogglProject):
                return
            project = proj

        self.cache.delete_entries(project)
        self.cache.commit()

    def edit(self, project: TogglProject | int, body: ProjectBody) -> TogglProject | None:
        """Edit a project based on its id with the parameters provided in the body.

        This endpoint always hit the external API in order to keep projects consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#put-workspaceproject)
        """
        if isinstance(project, TogglProject):
            project = project.id
        return self.request(
            f"/{project}",
            method=RequestMethod.PUT,
            body=body.format("edit", workspace_id=self.workspace_id),
            refresh=True,
        )

    def add(self, body: ProjectBody) -> TogglProject | None:
        """Create a new project based on the parameters provided in the body.

        This endpoint always hit the external API in order to keep projects consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#post-workspaceprojects)
        """
        if body.name is None:
            msg = "Name must be set in order to create a project!"
            raise NamingError(msg)

        return self.request(
            "",
            method=RequestMethod.POST,
            body=body.format("add", workspace_id=self.workspace_id),
            refresh=True,
        )

    @classmethod
    def get_color(cls, color: str) -> str:
        """Get a color by name. Defaults to gray."""
        return cls.BASIC_COLORS.get(color, "#525266")

    @classmethod
    def get_color_id(cls, color: str) -> int:
        """Get a color id by name."""
        colors = list(cls.BASIC_COLORS.values())
        return colors.index(color)

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/projects"

    @property
    def model(self) -> type[TogglProject]:
        return TogglProject
