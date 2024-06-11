from typing import Optional

from .meta import TogglCachedEndpoint
from .models import TogglWorkspace


class WorkspaceEndpoint(TogglCachedEndpoint):
    def get_workspace(self, *, refresh: bool = False) -> Optional[TogglWorkspace]:
        """Get the current workspace based on the workspace_id class attribute."""
        return self.request("", refresh=refresh)  # type: ignore[return-value]

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}"
