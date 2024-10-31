from __future__ import annotations

import logging

from httpx import HTTPStatusError, codes

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTag

log = logging.getLogger("toggl-api-wrapper.endpoint")


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

        This endpoint always hit the external API in order to keep tags consistent.

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

        This endpoint always hit the external API in order to keep tags consistent.

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

        This endpoint always hit the external API in order to keep tags consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#delete-delete-tag)
        """
        tag_id = tag if isinstance(tag, int) else tag.id
        try:
            self.request(
                f"/{tag_id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != codes.NOT_FOUND:
                raise
            log.warning(
                "Tag with id %s was either already deleted or did not exist in the first place!",
                tag_id,
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
