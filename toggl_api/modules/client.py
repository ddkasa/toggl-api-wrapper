from dataclasses import dataclass, field
from typing import Any, Optional

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglClient


@dataclass
class ClientBody:
    """JSON body dataclass for PUT, POST & PATCH requests."""

    workspace_id: Optional[int] = field(default=None)

    name: Optional[str] = field(default=None)
    """Name of the project. Defaults to None. Will be required if its a POST request."""
    status: Optional[str] = field(default=None)
    notes: Optional[str] = field(default=None)

    def format_body(self, workspace_id: int) -> dict[str, Any]:
        """Formats the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            workspace_id (int): Alternate Workspace ID for the request
                if the body does not contain a workspace_id.

        Returns:
            dict[str, Any]: JSON compatible formatted body.
        """
        body: dict[str, Any] = {
            "wid": self.workspace_id or workspace_id,
        }

        if self.name:
            body["name"] = self.name
        if self.status:
            body["status"] = self.status
        if self.notes:
            body["notes"] = self.notes
        return body


class ClientEndpoint(TogglCachedEndpoint):
    def create_client(self, body: ClientBody) -> Optional[TogglClient]:
        if body.name is None:
            msg = "Name must be set in order to create a client!"
            raise ValueError(msg)

        return self.request(
            "",
            body=body.format_body(self.workspace_id),
            method=RequestMethod.POST,
            refresh=True,
        )  # type: ignore[return-value]

    def get_client(
        self,
        client_id: int | TogglClient,
        *,
        refresh: bool = False,
    ) -> Optional[TogglClient]:
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
        return response or None  # type: ignore[return-value]

    def update_client(
        self,
        client: TogglClient | int,
        body: ClientBody,
    ) -> Optional[TogglClient]:
        if isinstance(client, TogglClient):
            client = client.id
        return self.request(
            f"/{client}",
            body=body.format_body(self.workspace_id),
            method=RequestMethod.PUT,
            refresh=True,
        )  # type: ignore[return-value]

    def delete_client(self, client: TogglClient | int) -> None:
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

    def get_clients(
        self,
        status: Optional[str] = None,
        name: Optional[str] = None,
        *,
        refresh: bool = False,
    ) -> list[TogglClient]:
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
        return response if isinstance(response, list) else []  # type: ignore[return-value]

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/clients"

    @property
    def model(self) -> type[TogglClient]:
        return TogglClient
