from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, cast, get_args

from httpx import Client, HTTPStatusError, Timeout, codes

from toggl_api._exceptions import NamingError
from toggl_api.meta.cache import TogglQuery

from .meta import BaseBody, RequestMethod, TogglCachedEndpoint
from .models import TogglClient

if TYPE_CHECKING:
    from httpx import BasicAuth

    from .meta.cache import TogglCache
    from .models import TogglWorkspace

log = logging.getLogger("toggl-api-wrapper.endpoint")


CLIENT_STATUS = Literal["active", "archived", "both"]


@dataclass
class ClientBody(BaseBody):
    """JSON body dataclass for PUT, POST & PATCH requests."""

    name: str | None = field(default=None)
    """Name of the client. Defaults to None. Will be required if its a POST request."""
    status: CLIENT_STATUS | None = field(default=None)
    """Status of the client. API defaults to active. Premium Feature."""
    notes: str | None = field(default=None)

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Format the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            endpoint: API endpoint for filtering purposes.
            body: Any additonal body content that the endpoint request requires.
                If passing workspace id to client endpoints use 'wid' instead.

        Returns:
            JSON compatible formatted body.
        """
        del endpoint
        if isinstance(self.name, str):
            body["name"] = self.name
        if self.status in get_args(CLIENT_STATUS):
            body["status"] = self.status
        if self.notes:
            body["notes"] = self.notes

        return body


class ClientEndpoint(TogglCachedEndpoint[TogglClient]):
    """Specific endpoints for retrieving and modifying clients.

    [Official Documentation](https://engineering.toggl.com/docs/api/clients)

    Examples:
        >>> wid = 123213324
        >>> client_endpoint = ClientEndpoint(wid, BasicAuth(...), SqliteCache(...))
        >>> client_endpoint.get(214125562)
        TogglClient(214125562, "Simplicidentata", workspace=123213324)

    Params:
        workspace_id: The workspace the clients belong to.
        auth: Authentication for the client.
        cache: Cache object where the clients will stored and handled.
        client: Optional client to be passed to be used for requests. Useful
            when a global client is used and needs to be recycled.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    MODEL = TogglClient

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: TogglCache[TogglClient] | None = None,
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

    def add(self, body: ClientBody) -> TogglClient:
        """Create a Client based on parameters set in the provided body.

        This endpoint always hit the external API in order to keep clients consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#post-create-client)

        Args:
            body: New parameters for the client to be created.

        Raises:
            NamingError: If no name was set as its required.

        Returns:
            Newly created client with specified parameters.
        """
        if body.name is None:
            msg = "Name must be set in order to create a client!"
            raise NamingError(msg)

        return cast(
            "TogglClient",
            self.request(
                self.endpoint,
                body=body.format("add", wid=self.workspace_id),
                method=RequestMethod.POST,
                refresh=True,
            ),
        )

    def get(self, client_id: int | TogglClient, *, refresh: bool = False) -> TogglClient | None:
        """Request a client based on its id.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#get-load-client-from-id)

        Args:
            client_id: Which client to look for.
            refresh: Whether to only check cache. It will default to True if id
                is not found in cache. Defaults to False.

        Raises:
            HTTPStatusError: Any error that is not a 404 code or `re_raise` is True.

        Returns:
            A TogglClient if the client was found else None.
        """
        if isinstance(client_id, TogglClient):
            client_id = client_id.id

        if self.cache and not refresh:
            return self.cache.find({"id": client_id})

        try:
            response = self.request(
                f"{self.endpoint}/{client_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                log.warning("Client with id %s does not exist!", client_id)
                return None
            raise

        return cast("TogglClient", response) or None

    def edit(self, client: TogglClient | int, body: ClientBody) -> TogglClient:
        """Edit a client with the supplied parameters from the body.

        This endpoint always hit the external API in order to keep clients consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#put-change-client)

        Args:
            client: Target client to edit.
            body: New parameters to use. Ignore client status.

        Returns:
            Newly edited client or None if not found.
        """
        if body.status:
            log.warning("Client status not supported by edit endpoint")
            body.status = None

        if isinstance(client, TogglClient):
            client = client.id

        return cast(
            "TogglClient",
            self.request(
                f"{self.endpoint}/{client}",
                body=body.format("edit", wid=self.workspace_id),
                method=RequestMethod.PUT,
                refresh=True,
            ),
        )

    def delete(self, client: TogglClient | int) -> None:
        """Delete a client based on its ID.

        This endpoint always hit the external API in order to keep clients consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#delete-delete-client)

        Raises:
            HTTPStatusError: If anything thats not an *ok* or *404* status code
                is returned.
        """
        client_id = client if isinstance(client, int) else client.id
        try:
            self.request(f"{self.endpoint}/{client_id}", method=RequestMethod.DELETE, refresh=True)
        except HTTPStatusError as err:
            if self.re_raise or err.response.status_code != codes.NOT_FOUND:
                raise
            log.warning(
                "Client with id %s was either already deleted or did not exist in the first place!",
                client_id,
            )
        if self.cache is None:
            return
        if isinstance(client, int):
            clt = self.cache.find({"id": client})
            if not isinstance(clt, TogglClient):
                return
            client = clt

        self.cache.delete(client)
        self.cache.commit()

    def _collect_cache(self, body: ClientBody | None) -> list[TogglClient]:
        if body and body.status is not None:
            log.warning("Client body 'status' parameter is not implemented with cache!")

        if body and body.name:
            return list(self.query(TogglQuery("name", body.name)))

        return list(self.load_cache())

    def collect(
        self,
        body: ClientBody | None = None,
        *,
        refresh: bool = False,
    ) -> list[TogglClient]:
        """Request all Clients based on status and name if specified in the body.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#get-list-clients)

        Args:
            body: Status and name to target. Ignores notes. Ignores status if using cache.
            refresh: Whether to refresh cache.

        Returns:
            A list of clients. Empty if not found.
        """
        if self.cache and not refresh:
            return self._collect_cache(body)

        url = self.endpoint
        if body and body.status:
            url += f"?{body.status}"
        if body and body.name:
            if body.status:
                url += "&"
            else:
                url += "?"
            url += f"{body.name}"

        response = self.request(url, method=RequestMethod.GET, refresh=refresh)
        return response if isinstance(response, list) else []

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/clients"
