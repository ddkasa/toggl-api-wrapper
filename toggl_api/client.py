import logging
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, get_args

from httpx import HTTPStatusError

from .meta import BaseBody, RequestMethod, TogglCachedEndpoint
from .models import TogglClient

log = logging.getLogger("toggl-api-wrapper.endpoint")


CLIENT_STATUS = Literal["active", "archived", "both"]


@dataclass
class ClientBody(BaseBody):
    """JSON body dataclass for PUT, POST & PATCH requests."""

    name: Optional[str] = field(default=None)
    """Name of the client. Defaults to None. Will be required if its a POST request."""
    status: Optional[CLIENT_STATUS] = field(default=None)
    """Status of the client. API defaults to active. Premium Feature."""
    notes: Optional[str] = field(default=None)

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Formats the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            endpoint: API endpoint for filtering purposes.
            body: Any additonal body content that the endpoint request requires.
                If passing workspace id to client endpoints use 'wid' instead.

        Returns:
            dict: JSON compatible formatted body.
        """

        if isinstance(self.name, str):
            body["name"] = self.name
        if self.status in get_args(CLIENT_STATUS):
            body["status"] = self.status
        if self.notes:
            body["notes"] = self.notes

        return body


class ClientEndpoint(TogglCachedEndpoint):
    """Specific endpoints for retrieving and modifying clients.

    [Official Documentation](https://engineering.toggl.com/docs/api/clients)
    """

    def add(self, body: ClientBody) -> TogglClient | None:
        """Create a Client based on parameters set in the provided body.

        This endpoint always hit the external API in order to keep clients consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#post-create-client)

        Args:
            body: New parameters for the client to be created.

        Raises:
            ValueError: If no name was set as its required.

        Returns:
            TogglClient: Newly created client with specified parameters.
        """

        if body.name is None:
            msg = "Name must be set in order to create a client!"
            raise ValueError(msg)

        return self.request(
            "",
            body=body.format("add", wid=self.workspace_id),
            method=RequestMethod.POST,
            refresh=True,
        )

    def get(self, client_id: int | TogglClient, *, refresh: bool = False) -> TogglClient | None:
        """Request a client based on its id.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#get-load-client-from-id)

        Args:
            client_id: Which client to look for.
            refresh: Whether to only check cache. It will default to True if id
                is not found in cache. Defaults to False.

        Returns:
            TogglClient | None: If the client was found.
        """
        if isinstance(client_id, TogglClient):
            client_id = client_id.id

        if not refresh:
            return self.cache.find_entry({"id": client_id})  # type: ignore[return-value]

        try:
            response = self.request(
                f"/{client_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if err.response.status_code == self.NOT_FOUND:
                log.warning("Client with id %s does not exist!", client_id)
                return None
            raise

        return response or None

    def edit(self, client: TogglClient | int, body: ClientBody) -> TogglClient | None:
        """Edit a client with the supplied parameters from the body.

        This endpoint always hit the external API in order to keep clients consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#put-change-client)

        Args:
            client: Target client to edit.
            body: New parameters to use. Ignore client status.

        Returns:
            TogglClient | None: Newly edited client or None if not found.
        """
        if body.status:
            log.warning("Client status not supported by edit endpoint")
            body.status = None

        if isinstance(client, TogglClient):
            client = client.id
        return self.request(
            f"/{client}",
            body=body.format("edit", wid=self.workspace_id),
            method=RequestMethod.PUT,
            refresh=True,
        )

    def delete(self, client: TogglClient | int) -> None:
        """Delete a client based on its ID.

        This endpoint always hit the external API in order to keep clients consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#delete-delete-client)
        """
        client_id = client if isinstance(client, int) else client.id
        try:
            self.request(f"/{client_id}", method=RequestMethod.DELETE, refresh=True)
        except HTTPStatusError as err:
            if err.response.status_code != self.NOT_FOUND:
                raise
            log.warning(
                "Client with id %s was either already deleted or did not exist in the first place!",
                client_id,
            )
        if isinstance(client, int):
            clt = self.cache.find_entry({"id": client})
            if not isinstance(clt, TogglClient):
                return
            client = clt

        self.cache.delete_entries(client)
        self.cache.commit()

    def collect(
        self,
        body: Optional[ClientBody] = None,
        *,
        refresh: bool = False,
    ) -> list[TogglClient]:
        """Request all Clients based on status and name if specified in the body.

        [Official Documentation](https://engineering.toggl.com/docs/api/clients#get-list-clients)

        Args:
            body: Status and name to target. Ignores notes.
            refresh: Whether to refresh cache.

        Returns:
            list[TogglClient]: A list of clients. Empty if not found.
        """
        url = ""
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

    @property
    def model(self) -> type[TogglClient]:
        return TogglClient
