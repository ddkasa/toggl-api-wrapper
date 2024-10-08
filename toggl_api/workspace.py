import warnings
from typing import Optional

from .meta import TogglCachedEndpoint
from .models import TogglWorkspace


class WorkspaceEndpoint(TogglCachedEndpoint):
    """Specific endpoints for retrieving workspaces."""

    def get(
        self,
        workspace: Optional[TogglWorkspace | int] = None,
        *,
        refresh: bool = False,
    ) -> TogglWorkspace | None:
        """Get the current workspace based on the workspace_id class attribute."""
        if workspace is None:
            workspace = self.workspace_id
        elif isinstance(workspace, TogglWorkspace):
            workspace = workspace.id

        if not refresh:
            tracker = self.cache.find_entry({"id": workspace})
            if isinstance(tracker, TogglWorkspace):
                return tracker
            refresh = True

        return self.request("", refresh=refresh)  # type: ignore[return-value]

    def get_workspace(
        self,
        workspace: Optional[TogglWorkspace | int] = None,
        *,
        refresh: bool = False,
    ) -> TogglWorkspace | None:
        warnings.warn("Deprecated in favour 'get' method.", DeprecationWarning, stacklevel=1)
        return self.get(workspace, refresh=refresh)

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}"
