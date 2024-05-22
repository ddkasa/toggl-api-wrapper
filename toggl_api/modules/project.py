from pathlib import Path
from typing import Any, Final

from .meta import RequestMethod, TogglCachedEndpoint, TogglEndpoint
from .models import TogglProject


class ProjectCachedEndpoint(TogglCachedEndpoint):
    def get_projects(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglProject] | None:
        response = self.request("", refresh=refresh)
        if response is None:
            return None

        return self.process_models(response)  # type: ignore[arg-type]

    def get_project(self, project_id: int) -> TogglProject:
        return self.model.from_kwargs(**self.request(f"/{project_id}"))  # type: ignore[arg-type]

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/projects"

    @property
    def model(self) -> type[TogglProject]:
        return TogglProject

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "projects.json"


class ProjectEndpoint(TogglEndpoint):
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

    def delete_project(self, project_id: int) -> None:
        self.request(f"/{project_id}", method=RequestMethod.DELETE)

    def edit_project(self, project_id: int, **kwargs) -> TogglProject | None:
        data = self.request(
            f"/{project_id}",
            method=RequestMethod.PUT,
            body=self.body_creation(**kwargs),
        )
        if data is None:
            return None

        return self.model.from_kwargs(**data)

    def add_project(self, **kwargs) -> TogglProject | None:
        data = self.request(
            "",
            method=RequestMethod.POST,
            body=self.body_creation(**kwargs),
        )
        if data is None:
            return None

        return self.model.from_kwargs(**data)

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/projects"

    @property
    def model(self) -> type[TogglProject]:
        return TogglProject

    @classmethod
    def get_color(cls, color: str) -> str:
        return cls.BASIC_COLORS.get(color, "#d80435")

    @classmethod
    def get_color_id(cls, color: str) -> int:
        colors = list(cls.BASIC_COLORS.values())
        return colors.index(color)
