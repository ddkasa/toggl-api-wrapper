from .meta import TogglCachedEndpoint
from .models import TogglWorkspace


class WorkspaceEndpoint(TogglCachedEndpoint):
    def get_workspace(self, *, refresh: bool = False) -> TogglWorkspace | None:
        response = self.request("", refresh=refresh)
        if not isinstance(response, list):
            return None
        return self.model.from_kwargs(**response[0])

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}"
