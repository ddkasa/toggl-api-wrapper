from dataclasses import dataclass, field
from typing import Any, Optional

from .meta import BaseBody, RequestMethod, TogglCachedEndpoint
from .models import TogglClient


@dataclass
class ClientBody(BaseBody):
    """JSON body dataclass for PUT, POST & PATCH requests."""

    name: Optional[str] = field(default=None)
    """Name of the client. Defaults to None. Will be required if its a POST request."""
    status: Optional[str] = field(default=None)
    notes: Optional[str] = field(default=None)

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Formats the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            endpoint: API endpoint for filtering purposes.
            body: Any additonal body content that the endpoint request requires.

        Returns:
            dict: JSON compatible formatted body.
        """

        if self.name:
            body["name"] = self.name
        if self.status:
            body["status"] = self.status
        if self.notes:
            body["notes"] = self.notes

        return body


class ClientEndpoint(TogglCachedEndpoint):
    """Specific endpoints for retrieving and modifying clients."""

    def add(self, body: ClientBody) -> TogglClient | None:
        """Create a Client based on parameters set in the provided body."""

        if body.name is None:
            msg = "Name must be set in order to create a client!"
            raise ValueError(msg)

        return self.request(
            "",
            body=body.format("add", wid=self.workspace_id),
            method=RequestMethod.POST,
            refresh=True,
        )

    def get(
        self,
        client_id: int | TogglClient,
        *,
        refresh: bool = False,
    ) -> TogglClient | None:
        """Request a client based on its id.

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
            client = self.cache.find_entry({"id": client_id})
            if isinstance(client, TogglClient):
                return client
            refresh = True

        response = self.request(
            f"/{client_id}",
            refresh=refresh,
        )
        return response or None

    def edit(
        self,
        client: TogglClient | int,
        body: ClientBody,
    ) -> TogglClient | None:
        """Edit a client with the supplied parameters from the body."""
        if isinstance(client, TogglClient):
            client = client.id
        return self.request(
            f"/{client}",
            body=body.format("edit", wid=self.workspace_id),
            method=RequestMethod.PUT,
            refresh=True,
        )

    def delete(self, client: TogglClient | int) -> None:
        """Delete a client based on its ID."""
        self.request(
            f"/{client if isinstance(client, int) else client.id}",
            method=RequestMethod.DELETE,
            refresh=True,
        )
        if isinstance(client, int):
            client = self.cache.find_entry({"id": client})  # type: ignore[assignment]
            if not isinstance(client, TogglClient):
                return

        self.cache.delete_entries(client)
        self.cache.commit()

    def collect(
        self,
        status: Optional[str] = None,
        name: Optional[str] = None,
        *,
        refresh: bool = False,
    ) -> list[TogglClient]:
        """Request all Clients based on status and name if specified."""
        url = ""
        if status:
            url += f"?{status}"
        if name:
            if status:
                url += "&"
            else:
                url += "?"
            url += f"{name}"

        response = self.request(url)
        return response if isinstance(response, list) else []

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/clients"

    @property
    def model(self) -> type[TogglClient]:
        return TogglClient
