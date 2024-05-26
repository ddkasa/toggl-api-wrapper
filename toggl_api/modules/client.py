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

        response = self.request("", body=body, method=RequestMethod.POST)
        if response is None:
            return None

        return self.model.from_kwargs(**response[0])

    def get_client(self, client_id: int) -> TogglClient | None:
        response = self.request(f"/{client_id}")

        if response is None:
            return None

        return self.model.from_kwargs(**response[0])

    def update_client(self, client_id: int, **kwargs) -> TogglClient:
        body = self.body_creation(**kwargs)
        response = self.request(
            f"/{client_id}",
            body=body,
            method=RequestMethod.PUT,
        )

        if response is None:
            return None

        return self.model.from_kwargs(**response[0])

    def delete_client(self, client_id: int) -> None:
        self.request(f"/{client_id}", method=RequestMethod.DELETE)

    def get_clients(self, **kwargs) -> list[TogglClient] | None:
        url = ""

        status = kwargs.get("status")
        name = kwargs.get("name")

        if status:
            url += f"?{status}"
        if name:
            if status:
                url += "&"
            else:
                url += "?"
            url += f"{name}"

        response = self.request(url)

        if response is None:
            return None

        return self.process_models(response)

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/clients"

    @property
    def model(self) -> type[TogglClient]:
        return TogglClient
