from pathlib import Path

from .meta import TogglCachedEndpoint
from .models import TogglWorkspace


class CachedWorkspaceEndpoint(TogglCachedEndpoint):
    def get_workspace(self, *, refresh: bool = False) -> TogglWorkspace | None:
        response = self.request("", refresh=refresh)
        if not isinstance(response, dict):
            return None
        return self.model.from_kwargs(**response)

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}"

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "workspace.json"
