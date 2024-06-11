from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTag


class TagEndpoint(TogglCachedEndpoint):
    def get_tags(
        self,
        *,
        refresh: bool = False,
    ) -> list[TogglTag]:
        return self.request("", refresh=refresh)  # type: ignore[return-value]

    def create_tag(self, name: str) -> TogglTag:
        return self.request(
            "",
            body={"name": name},
            method=RequestMethod.POST,
            refresh=True,
        )  # type: ignore[return-value]

    def update_tag(
        self,
        tag: TogglTag,
    ) -> TogglTag:
        """Sets the name of the tag based on the tag object."""
        return self.request(
            f"/{tag.id}",
            body={"name": tag.name},
            method=RequestMethod.PUT,
            refresh=True,
        )  # type: ignore[return-value]

    def delete_tag(self, tag: TogglTag, **kwargs) -> None:
        """Deletes a tag based on its id."""
        self.request(f"/{tag.id}", method=RequestMethod.DELETE, refresh=True)
        self.cache.delete_entries(tag)
        self.cache.commit()

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/tags"

    @property
    def model(self) -> type[TogglTag]:
        return TogglTag
