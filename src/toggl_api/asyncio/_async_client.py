from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from httpx import AsyncClient, HTTPStatusError, codes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toggl_api import ClientBody, NamingError, TogglClient
from toggl_api.meta import RequestMethod

from ._async_endpoint import TogglAsyncCachedEndpoint

if TYPE_CHECKING:
    from httpx import BasicAuth
    from sqlalchemy.engine import ScalarResult
    from sqlalchemy.sql.expression import ColumnElement

    from toggl_api import TogglWorkspace

    from ._async_sqlite_cache import AsyncSqliteCache

log = logging.getLogger("toggl-api-wrapper.endpoint")


class AsyncClientEndpoint(TogglAsyncCachedEndpoint[TogglClient]):
    """Specific endpoints for retrieving and modifying clients.

    [Official Documentation](https://engineering.toggl.com/docs/api/clients)

    Examples:
        >>> wid = 123213324
        >>> client_endpoint = AsyncClientEndpoint(wid, BasicAuth(...), AsyncSqliteCache(...))
        >>> await client_endpoint.get(214125562)
        TogglClient(214125562, "Simplicidentata", workspace=123213324)

    Params:
        workspace_id: The workspace the clients belong to.
        auth: Authentication for the client.
        cache: Cache object where the clients will stored and handled.
        client: Optional async client to be passed to be used for requests.
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
        cache: AsyncSqliteCache[TogglClient] | None = None,
        *,
        client: AsyncClient | None = None,
        timeout: int = 10,
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

    async def add(self, body: ClientBody) -> TogglClient:
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

        response = await self.request(
            self.endpoint,
            body=body.format("add", wid=self.workspace_id),
            method=RequestMethod.POST,
            refresh=True,
        )

        return cast("TogglClient", response)

    async def get(
        self,
        client_id: int | TogglClient,
        *,
        refresh: bool = False,
    ) -> TogglClient | None:
        """Request a client based on its id.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#get-load-client-from-id)

        Args:
            client_id: Which client to look for.
            refresh: Whether to only check cache. It will default to True if id
                is not found in cache. Defaults to False.

        Raises:
            HTTPStatusError: If anything thats not 'ok' or a 404 is returned.

        Returns:
            A TogglClient if the client was found else None.
        """
        if isinstance(client_id, TogglClient):
            client_id = client_id.id

        if self.cache and not refresh:
            return await self.cache.find(client_id)

        try:
            response = await self.request(
                f"{self.endpoint}/{client_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                log.warning("Client with id %s does not exist!", client_id)
                return None
            raise

        return cast("TogglClient | None", response)

    async def edit(
        self,
        client: TogglClient | int,
        body: ClientBody,
    ) -> TogglClient:
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

        response = await self.request(
            f"{self.endpoint}/{client}",
            body=body.format("edit", wid=self.workspace_id),
            method=RequestMethod.PUT,
            refresh=True,
        )

        return cast("TogglClient", response)

    async def delete(self, client: TogglClient | int) -> None:
        """Delete a client based on its ID.

        This endpoint always hit the external API in order to keep clients consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#delete-delete-client)

        Raises:
            HTTPStatusError: If anything thats not an *ok* or *404* status code
                is returned.
        """
        client_id = client if isinstance(client, int) else client.id
        try:
            await self.request(
                f"{self.endpoint}/{client_id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
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
            clt = await self.cache.find(client)
            if not isinstance(clt, TogglClient):
                return
            client = clt

        await self.cache.delete(client)

    async def _collect_cache(
        self,
        body: ClientBody | None,
    ) -> ScalarResult[TogglClient]:
        if body and body.status is not None:
            log.warning(
                "Client body 'status' parameter is not implemented with cache!",
            )

        statement = select(TogglClient)
        if body and body.name:
            statement = statement.filter(
                cast("ColumnElement[bool]", TogglClient.name == body.name),
            )

        cache = cast("AsyncSqliteCache[TogglClient]", self.cache)
        async with AsyncSession(
            cache.database,
            expire_on_commit=False,
        ) as session:
            return (await session.execute(statement)).scalars()

    async def collect(
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
            return list((await self._collect_cache(body)).fetchall())

        url = self.endpoint
        if body and body.status:
            url += f"?{body.status}"
        if body and body.name:
            if body.status:
                url += "&"
            else:
                url += "?"
            url += f"{body.name}"

        response = await self.request(
            url,
            method=RequestMethod.GET,
            refresh=refresh,
        )
        return cast("list[TogglClient]", response)

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/clients"
