from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Final, Optional

from toggl_api.utility import format_iso

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglProject


@dataclass
class ProjectBody:
    """JSON body dataclass for PUT, POST & PATCH requests."""

    workspace_id: Optional[int] = field(default=None)
    name: Optional[str] = field(default=None)
    """Name of the project. Defaults to None. Will be required if its a POST request."""

    active: bool = field(default=True)
    """Whether the project is archived or active."""
    is_private: Optional[bool] = field(default=True)
    """Whether the project is private or not. Defaults to True."""

    client_id: Optional[int] = field(default=None)
    client_name: Optional[str] = field(default=None)
    """Client name if client_id is not set. Defaults to None. If client_id is
    set the client_name will be ignored."""

    color: Optional[str] = field(default=None)

    start_date: Optional[datetime | date] = field(default=None)
    end_date: Optional[datetime | date] = field(default=None)
    """Date to set the end of the project. If not set or start date is after
    the end date the end date will be ignored."""

    def format_body(self, workspace_id: int) -> dict[str, Any]:
        """Formats the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            workspace_id (int): Alternate Workspace ID for the request
                if the body does not contain a workspace_id.

        Returns:
            dict[str, Any]: JSON compatible formatted body.
        """
        headers: dict[str, Any] = {
            "workspace_id": self.workspace_id or workspace_id,
            "active": self.active,
            "is_private": self.is_private,
        }

        if self.client_id:
            headers["client_id"] = self.client_id
        elif self.client_name:
            headers["client_name"] = self.client_name
        if self.color:
            color = ProjectEndpoint.get_color(self.color) if self.color in ProjectEndpoint.BASIC_COLORS else self.color
            headers["color"] = color
        if self.start_date:
            headers["start_date"] = format_iso(self.start_date)
            if self.end_date and self.end_date > self.start_date:
                headers["end_date"] = format_iso(self.end_date)

        if self.name:
            headers["name"] = self.name

        return headers


class ProjectEndpoint(TogglCachedEndpoint):
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
        "gray": "#d80435",
    }

    def get_projects(
        self,
        *,
        refresh: bool = False,
    ) -> Optional[list[TogglProject]]:
        return self.request("", refresh=refresh)  # type: ignore[return-value]

    def get_project(
        self,
        project_id: int | TogglProject,
        *,
        refresh: bool = False,
    ) -> Optional[TogglProject]:
        if isinstance(project_id, TogglProject):
            project_id = project_id.id

        if not refresh:
            project = self.cache.find_entry({"id": project_id})
            if isinstance(project, TogglProject):
                return project
            refresh = True

        response = self.request(
            f"/{project_id}",
            refresh=refresh,
        )

        return response or None  # type: ignore[return-value]

    def delete_project(self, project: TogglProject | int) -> None:
        self.request(
            f"/{project if isinstance(project, int) else project.id}",
            method=RequestMethod.DELETE,
            refresh=True,
        )

        if isinstance(project, int):
            project = self.cache.find_entry({"id": project})  # type: ignore[assignment]
            if not isinstance(project, TogglProject):
                return
        self.cache.delete_entries(project)
        self.cache.commit()

    def edit_project(
        self,
        project: TogglProject | int,
        body: ProjectBody,
    ) -> Optional[TogglProject]:
        if isinstance(project, TogglProject):
            project = project.id
        return self.request(
            f"/{project}",
            method=RequestMethod.PUT,
            body=body.format_body(self.workspace_id),
            refresh=True,
        )  # type: ignore[return-value]

    def add_project(
        self,
        body: ProjectBody,
    ) -> Optional[TogglProject]:
        if body.name is None:
            msg = "Name must be set in order to create a project!"
            raise ValueError(msg)
        return self.request(
            "",
            method=RequestMethod.POST,
            body=body.format_body(self.workspace_id),
            refresh=True,
        )  # type: ignore[return-value]

    @classmethod
    def get_color(cls, color: str) -> str:
        return cls.BASIC_COLORS.get(color, "#d80435")

    @classmethod
    def get_color_id(cls, color: str) -> int:
        colors = list(cls.BASIC_COLORS.values())
        return colors.index(color)

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/projects"

    @property
    def model(self) -> type[TogglProject]:
        return TogglProject
