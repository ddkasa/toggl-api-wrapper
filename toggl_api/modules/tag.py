from pathlib import Path
from typing import Any

from .meta import RequestMethod, TogglCachedEndpoint, TogglEndpoint
from .models import TogglTag


class TagCachedEndpoint(TogglCachedEndpoint):
    def get_tags(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglTag]:
        response = self.request("", refresh=refresh)
        if response is None:
            return []

        return self.process_models(response)  # type: ignore[arg-type]

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/tags"

    @property
    def model(self) -> type[TogglTag]:
        return TogglTag

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "tags.json"


class TagEndpoint(TogglEndpoint):
    def body_creation(self, **kwargs) -> dict[str, Any]:
        headers = super().body_creation(**kwargs)
        tag_id = kwargs.get("tag_id")
        name = kwargs.get("name")
        if name:
            headers["name"] = name
        if tag_id:
            headers["tag_id"] = tag_id

        return headers

    def create_tag(self, name: str, **kwargs) -> TogglTag:
        body = self.body_creation(**kwargs)
        body["name"] = name
        response = self.request("", body=body, method=RequestMethod.POST)
        return self.model.from_kwargs(**response)  # type: ignore[arg-type]

    def update_tag(self, tag_id: str, **kwargs) -> TogglTag:
        body = self.body_creation(**kwargs)
        response = self.request(f"/{tag_id}", body=body, method=RequestMethod.PUT)
        return self.model.from_kwargs(**response)  # type: ignore[arg-type]

    def delete_tag(self, tag_id: int, **kwargs) -> None:
        self.request(f"/{tag_id}", method=RequestMethod.DELETE)

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/tags"

    @property
    def model(self) -> type[TogglTag]:
        return TogglTag
