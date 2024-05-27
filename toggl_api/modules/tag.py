from typing import Any

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTag


class TagEndpoint(TogglCachedEndpoint):
    def get_tags(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglTag]:
        return self.request("", refresh=refresh)

    def create_tag(self, name: str, **kwargs) -> TogglTag:
        body = self.body_creation(**kwargs)
        body["name"] = name
        return self.request(
            "",
            body=body,
            method=RequestMethod.POST,
            refresh=True,
        )

    def update_tag(self, tag: TogglTag, **kwargs) -> TogglTag:
        body = self.body_creation(**kwargs)
        return self.request(
            f"/{tag.id}",
            body=body,
            method=RequestMethod.PUT,
            refresh=True,
        )

    def delete_tag(self, tag: TogglTag, **kwargs) -> None:
        self.request(f"/{tag.id}", method=RequestMethod.DELETE, refresh=True)
        self.cache.delete_entry(tag)

    def body_creation(self, **kwargs) -> dict[str, Any]:
        headers = super().body_creation(**kwargs)
        tag_id = kwargs.get("tag_id")
        name = kwargs.get("name")
        if name:
            headers["name"] = name
        if tag_id:
            headers["tag_id"] = tag_id

        return headers

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/tags"

    @property
    def model(self) -> type[TogglTag]:
        return TogglTag
