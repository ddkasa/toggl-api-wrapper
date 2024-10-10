from __future__ import annotations

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTag


class TagEndpoint(TogglCachedEndpoint):
    """Specific endpoints for retrieving and modifying tags.

    [Official Documentation](https://engineering.toggl.com/docs/api/tags)
    """

    def collect(self, *, refresh: bool = False) -> list[TogglTag]:
        """Gather all tags.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#get-tags)
        """
        return self.request("", refresh=refresh)

    def add(self, name: str) -> TogglTag:
        """Create a new tag.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#post-create-tag)
        """
        return self.request(
            "",
            body={"name": name},
            method=RequestMethod.POST,
            refresh=True,
        )

    def edit(self, tag: TogglTag) -> TogglTag:
        """Sets the name of the tag based on the tag object.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#put-update-tag)
        """
        return self.request(
            f"/{tag.id}",
            body={"name": tag.name},
            method=RequestMethod.PUT,
            refresh=True,
        )

    def delete(self, tag: TogglTag | int) -> None:
        """Deletes a tag based on its ID.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#delete-delete-tag)
        """
        self.request(
            f"/{tag if isinstance(tag, int) else tag.id}",
            method=RequestMethod.DELETE,
            refresh=True,
        )

        if isinstance(tag, int):
            tag_model = self.cache.find_entry({"id": tag})
            if not isinstance(tag_model, TogglTag):
                return
            tag = tag_model

        self.cache.delete_entries(tag)
        self.cache.commit()

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/tags"

    @property
    def model(self) -> type[TogglTag]:
        return TogglTag
