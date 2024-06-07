from typing import Any, Final, Optional

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglProject


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
        **kwargs,
    ) -> Optional[list[TogglProject]]:
        return self.request("", refresh=refresh)  # type: ignore[return-value]

    def get_project(
        self,
        project_id: int,
        *,
        refresh: bool = False,
    ) -> Optional[TogglProject]:
        return self.request(
            f"/{project_id}",
            refresh=refresh,
        )  # type: ignore[return-value]

    def body_creation(self, **kwargs) -> dict[str, Any]:
        headers = super().body_creation(**kwargs)

        active = kwargs.get("active")
        client_id = kwargs.get("client_id")
        client_name = kwargs.get("client_name")
        color = kwargs.get("color")
        end_date = kwargs.get("end_date")
        is_private = kwargs.get("is_private")
        name = kwargs.get("name")
        start_date = kwargs.get("start_date")

        if active is not None:
            headers["active"] = active
        if client_id:
            headers["client_id"] = client_id
        if client_name:
            headers["client_name"] = client_name
        if color:
            if color in self.BASIC_COLORS:
                color = ProjectEndpoint.get_color(color)
            headers["color"] = color
        if end_date:
            headers["end_date"] = end_date
        if is_private is not None:
            headers["is_private"] = is_private
        if name:
            headers["name"] = name
        if start_date:
            headers["start_date"] = start_date
        return headers

    def delete_project(self, project: TogglProject) -> None:
        self.request(
            f"/{project.id}",
            method=RequestMethod.DELETE,
            refresh=True,
        )
        self.cache.delete_entries(project)
        self.cache.commit()

    def edit_project(self, project: TogglProject, **kwargs) -> Optional[TogglProject]:
        return self.request(
            f"/{project.id}",
            method=RequestMethod.PUT,
            body=self.body_creation(**kwargs),
            refresh=True,
        )  # type: ignore[return-value]

    def add_project(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> TogglProject | None:
        return self.request(
            "",
            method=RequestMethod.POST,
            body=self.body_creation(**kwargs),
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
        return super().endpoint + f"workspaces/{self.workspace_id}/projects"

    @property
    def model(self) -> type[TogglProject]:
        return TogglProject
