from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, Any, Optional

from httpx import HTTPStatusError, codes

from ._exceptions import NamingError
from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTag

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api.meta import TogglCache

    from .models import TogglWorkspace

log = logging.getLogger("toggl-api-wrapper.endpoint")


class TagEndpoint(TogglCachedEndpoint[TogglTag]):
    """Specific endpoints for retrieving and modifying tags.

    Tags don't have single model get endpoint. Use parent class query method
    if searching for a single tag.

    [Official Documentation](https://engineering.toggl.com/docs/api/tags)

    Examples:
        >>> tag_endpoint = TagEndpoint(21341214, BasicAuth(...), JSONCache(Path("cache")))
        >>> tag_endpoint.add("Eucalyptus")
        TogglTag(213123132, "Eucalyptus")

        >>> tag_endpoint.query(TogglQuery("name", "Eucalyptus"))
        [TogglTag(213123132, "Eucalyptus")]

    Params:
        workspace_id: The workspace the tags belong to.
    """

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: TogglCache[TogglTag],
        *,
        timeout: int = 20,
        **kwargs: Any,
    ) -> None:
        super().__init__(0, auth, cache, timeout=timeout, **kwargs)
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    def collect(self, *, refresh: bool = False) -> list[TogglTag]:
        """Gather all tags.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#get-tags)
        """
        return self.request("", refresh=refresh)

    def add(self, name: str) -> TogglTag:
        """Create a new tag.

        This endpoint always hit the external API in order to keep tags consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#post-create-tag)

        Args:
            name: The name of the new tag.

        Raises:
            NamingError: IF the tag name is empty.
            HTTPStatusError: If a tag with the same name exists.

        Returns:
            TogglTag: The newly created tag.
        """

        if not name:
            msg = "The tag name needs to be at least one character long."
            raise NamingError(msg)

        return self.request(
            "",
            body={"name": name},
            method=RequestMethod.POST,
            refresh=True,
        )

    def edit(self, tag: TogglTag | int, name: Optional[str] = None) -> TogglTag:
        """Sets the name of the tag based on the tag object.

        This endpoint always hit the external API in order to keep tags consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#put-update-tag)

        Examples:
            >>> tag = Tag(213123132, "Eucalyptus")
            >>> tag_endpoint.edit(tag)
            TogglTag(213123132, "Eucalyptus")

            >>> tag_endpoint.edit(213123132, "Eucalyptus")
            TogglTag(213123132, "Eucalyptus")

        Args:
            tag: TogglTag or integer as the id.
                *Currently can accept the tag as the 'name' input as well.*
            name: New name for the tag. Will become required in the next major
                version.

        Raises:
            NamingError: If the name is not at the minimum length.
            HTTPStatusError: If any issue happens with the Toggl API.

        Returns:
            TogglTag: The edited tag.
        """

        if isinstance(tag, TogglTag) and name is None:
            warnings.warn(
                "DEPRECATED: the 'name' argument will replace the internal usage of the 'Tag.name' attribute.",
                stacklevel=2,
            )
            name = tag.name

        if not name:
            msg = "The tag name needs to be at least one character long."
            raise NamingError(msg)

        return self.request(
            f"/{tag.id if isinstance(tag, TogglTag) else tag}",
            body={"name": name},
            method=RequestMethod.PUT,
            refresh=True,
        )

    def delete(self, tag: TogglTag | int) -> None:
        """Deletes a tag based on its ID or model.

        This endpoint always hit the external API in order to keep tags consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#delete-delete-tag)

        Args:
            tag: The tag to delete. Either the id or model.

        Raises:
            HTTPStatusError: For anything thats not an '2xx' or '404' code.
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
