from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from httpx import Client, HTTPStatusError, Timeout, codes

from toggl_api.meta.cache import TogglQuery

from ._exceptions import NamingError
from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTag

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api.meta.cache import TogglCache

    from .models import TogglWorkspace

log = logging.getLogger("toggl-api-wrapper.endpoint")


class TagEndpoint(TogglCachedEndpoint[TogglTag]):
    """Specific endpoints for retrieving and modifying tags.

    [Official Documentation](https://engineering.toggl.com/docs/api/tags)

    Examples:
        >>> tag_endpoint = TagEndpoint(21341214, BasicAuth(...), JSONCache(Path("cache")))
        >>> tag_endpoint.add("Eucalyptus")
        TogglTag(213123132, "Eucalyptus")

        >>> tag_endpoint.query(TogglQuery("name", "Eucalyptus"))
        [TogglTag(213123132, "Eucalyptus")]

    Params:
        workspace_id: The workspace the tags belong to.
        auth: Authentication for the client.
        cache: Cache object where tags are stored.
        client: Optional client to be passed to be used for requests. Useful
            when a global client is used and needs to be recycled.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only
    """

    MODEL = TogglTag

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: TogglCache[TogglTag] | None = None,
        *,
        client: Client | None = None,
        timeout: Timeout | int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(
            auth,
            cache,
            client=client,
            timeout=timeout,
            re_raise=re_raise,
            retries=retries,
        )
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    def get(
        self,
        tag: TogglTag | int,
        *,
        refresh: bool = False,
    ) -> TogglTag | None:
        """Get endpoint convenience method for querying single tags from cache.

        This endpoint doesn't exist on the API so it locally queries for tags
        instead.

        Examples:
            >>> toggl_endpoint.get(213123132)
            TogglTag(213123132, "Eucalyptus")

        Args:
            tag: Which tag to retrieve. Can be an existing model or its id.
            refresh: Whether to collect all tags from the API first.

        Raises:
            HTTPStatusError: If an error is raised and `re_raise` is True.

        Returns:
            A tag model if it was found otherwise None.
        """
        if self.cache is None:
            return None

        if refresh:
            try:
                self.collect(refresh=True)
            except HTTPStatusError:
                if self.re_raise:
                    raise
                log.exception("%s")

        if isinstance(tag, TogglTag):
            tag = tag.id

        query = self.query(TogglQuery("id", tag))
        if query:
            return query[0]

        return None

    def collect(self, *, refresh: bool = False) -> list[TogglTag]:
        """Gather all tags.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#get-tags)

        Raises:
            HTTPStatusError: If any issue happens with the Toggl API.

        Returns:
            A list of tags collected from the API or local cache.
        """
        return cast("list[TogglTag]", self.request(self.endpoint, refresh=refresh))

    def add(self, name: str) -> TogglTag:
        """Create a new tag.

        This endpoint always hit the external API in order to keep tags consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/tags#post-create-tag)

        Args:
            name: The name of the new tag.

        Raises:
            NamingError: IF the tag name is empty.
            HTTPStatusError: If a tag with the same name exists or any other
                none *ok* status code is returned.

        Returns:
            The newly created tag.
        """
        if not name:
            msg = "The tag name needs to be at least one character long."
            raise NamingError(msg)

        return cast(
            "TogglTag",
            self.request(
                self.endpoint,
                body={"name": name},
                method=RequestMethod.POST,
                refresh=True,
            ),
        )

    def edit(self, tag: TogglTag | int, name: str) -> TogglTag:
        """Set the name of the tag based on the tag object.

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
            name: New name for the tag.

        Raises:
            NamingError: If the name is not at the minimum length.
            HTTPStatusError: If any issue happens with the Toggl API.

        Returns:
            The edited tag.
        """
        if not name:
            msg = "The tag name needs to be at least one character long."
            raise NamingError(msg)

        return cast(
            "TogglTag",
            self.request(
                f"{self.endpoint}/{tag.id if isinstance(tag, TogglTag) else tag}",
                body={"name": name},
                method=RequestMethod.PUT,
                refresh=True,
            ),
        )

    def delete(self, tag: TogglTag | int) -> None:
        """Delete a tag based on its ID or model.

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
                f"{self.endpoint}/{tag_id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if self.re_raise or err.response.status_code != codes.NOT_FOUND:
                raise
            log.warning(
                "Tag with id %s was either already deleted or did not exist in the first place!",
                tag_id,
            )

        if self.cache is None:
            return

        if isinstance(tag, int):
            tag_model = self.cache.find({"id": tag})
            if not isinstance(tag_model, TogglTag):
                return
            tag = tag_model

        self.cache.delete(tag)
        self.cache.commit()

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/tags"
