from typing import Optional

from .meta import TogglCachedEndpoint
from .models import TogglWorkspace


class WorkspaceEndpoint(TogglCachedEndpoint):
    """Specific endpoints for retrieving workspaces.

    [Official Documentation](https://engineering.toggl.com/docs/api/workspaces)
    """

    def get(
        self,
        workspace: Optional[TogglWorkspace | int] = None,
        *,
        refresh: bool = False,
    ) -> TogglWorkspace | None:
        """Get the current workspace based on the workspace_id class attribute.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#get-get-single-workspace)
        """
        if workspace is None:
            workspace = self.workspace_id
        elif isinstance(workspace, TogglWorkspace):
            workspace = workspace.id

        if not refresh:
            return self.cache.find_entry({"id": workspace})  # type: ignore[return-value]

        return self.request(f"{workspace}", refresh=refresh)

    @property
    def model(self) -> type[TogglWorkspace]:
        return TogglWorkspace

    @property
    def endpoint(self) -> str:
        return "workspaces/"
