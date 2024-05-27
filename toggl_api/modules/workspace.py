from typing import Optional

from .meta import TogglCachedEndpoint
from .models import TogglWorkspace


class WorkspaceEndpoint(TogglCachedEndpoint):
    def get_workspace(self, *, refresh: bool = False) -> Optional[TogglWorkspace]:
        return self.request("", refresh=refresh)

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}"
