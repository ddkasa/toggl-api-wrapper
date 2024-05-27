from typing import Any

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglClient


class ClientEndpoint(TogglCachedEndpoint):
    def body_creation(self, **kwargs) -> dict[str, Any]:
        headers = super().body_creation(**kwargs)

        headers["wid"] = self.workspace_id

        status = kwargs.get("status")
        name = kwargs.get("name")
        notes = kwargs.get("notes")

        if name:
            headers["name"] = name
        if status:
            headers["status"] = status
        if notes:
            headers["notes"] = notes

        return headers

    def create_client(self, **kwargs) -> TogglClient | None:
        body = self.body_creation(**kwargs)
        return self.request(
            "",
            body=body,
            method=RequestMethod.POST,
            refresh=True,
        )

    def get_client(
        self,
        client_id: int,
        *,
        refresh: bool = False,
    ) -> TogglClient | None:
        return self.request(f"/{client_id}", refresh=refresh)

    def update_client(self, client_id: int, **kwargs) -> TogglClient:
        body = self.body_creation(**kwargs)
        response = self.request(
            f"/{client_id}",
            body=body,
            method=RequestMethod.PUT,
            refresh=True,
        )

        if response is None:
            return None

        return response

    def delete_client(self, client: TogglClient) -> None:
        self.request(
            f"/{client.id}",
            method=RequestMethod.DELETE,
            refresh=True,
        )
        self.cache.delete_entry(client)

    def get_clients(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglClient] | None:
        status = kwargs.get("status")
        name = kwargs.get("name")

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
        return super().endpoint + f"workspaces/{self.workspace_id}/clients"

    @property
    def model(self) -> type[TogglClient]:
        return TogglClient
