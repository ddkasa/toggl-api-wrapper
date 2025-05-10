"""All endpoint functionality related modifiying and handling workspaces."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, cast

from httpx import AsyncClient, HTTPStatusError, Response, codes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toggl_api import DateTimeError, TogglWorkspace
from toggl_api.meta import RequestMethod
from toggl_api.utility import get_timestamp

from ._async_endpoint import TogglAsyncCachedEndpoint

if TYPE_CHECKING:
    from httpx import BasicAuth
    from sqlalchemy.engine import ScalarResult
    from sqlalchemy.sql.expression import ColumnElement

    from toggl_api import TogglOrganization, WorkspaceBody, WorkspaceStatistics

    from ._async_sqlite_cache import AsyncSqliteCache


log = logging.getLogger("toggl-api-wrapper.endpoint")


class AsyncWorkspaceEndpoint(TogglAsyncCachedEndpoint[TogglWorkspace]):
    """Specific endpoints for retrieving and modifying workspaces.

    [Official Documentation](https://engineering.toggl.com/docs/api/workspaces)

    Examples:
        >>> org_id = 123213324
        >>> workspace_endpoint = AsyncWorkspaceEndpoint(org_id, BasicAuth(...), AsyncSqliteCache(...))

    Params:
        organization_id: Workspace endpoint takes an organization id instead of
            a workspace id.
        auth: Authentication for the client.
        client: Optional async client to be passed to be used for requests.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    MODEL = TogglWorkspace

    def __init__(
        self,
        organization_id: int | TogglOrganization,
        auth: BasicAuth,
        cache: AsyncSqliteCache[TogglWorkspace] | None = None,
        *,
        client: AsyncClient | None = None,
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(
            auth,
            cache,
            client=client,
            timeout=timeout,
            re_raise=re_raise,
            retries=retries,
        )
        self.organization_id = organization_id if isinstance(organization_id, int) else organization_id.id

    async def get(
        self,
        workspace: TogglWorkspace | int,
        *,
        refresh: bool = False,
    ) -> TogglWorkspace | None:
        """Get the current workspace based on an id or model.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#get-get-single-workspace)

        Args:
            workspace: Workspace id or model.
            refresh: Whether to use cache or not.

        Raises:
            HTTPStatusError: If anything that's not a '2xx' or '404' status_code is returned.

        Returns:
            Model of workspace if found else none.
        """
        if isinstance(workspace, TogglWorkspace):
            workspace = workspace.id

        if self.cache and not refresh:
            return await self.cache.find(workspace)

        try:
            response = await self.request(
                f"workspaces/{workspace}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            log.exception("%s")
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                return None
            raise

        return cast("TogglWorkspace", response)

    async def add(self, body: WorkspaceBody) -> TogglWorkspace:
        """Create a new workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#post-create-a-new-workspace)

        Enterprise plan feature.

        Args:
            body: All settings for the workspace to be attached to as a body.

        Returns:
            A newly created workspace with the supplied params.
        """
        response = await self.request(
            f"organizations/{self.organization_id}/workspaces",
            body=body.format("add", organization_id=self.organization_id),
            method=RequestMethod.POST,
            refresh=True,
        )
        return cast("TogglWorkspace", response)

    async def _collect_cache(
        self,
        since: int | None,
    ) -> ScalarResult[TogglWorkspace]:
        statement = select(TogglWorkspace)
        if isinstance(since, int):
            ts = datetime.fromtimestamp(since, timezone.utc)
            statement = statement.filter(
                cast("ColumnElement[bool]", TogglWorkspace.timestamp > ts),
            )

        cache = cast("AsyncSqliteCache[TogglWorkspace]", self.cache)
        async with AsyncSession(
            cache.database,
            expire_on_commit=False,
        ) as session:
            return (await session.execute(statement)).scalars()

    def _validate_collect_since(self, since: datetime | int) -> int:
        since = get_timestamp(since)
        now = int(time.mktime(datetime.now(tz=timezone.utc).timetuple()))
        if since > now:
            msg = "The 'since' argument needs to be before the current time!"
            raise DateTimeError(msg)
        return since

    async def collect(
        self,
        since: datetime | int | None = None,
        *,
        refresh: bool = False,
    ) -> list[TogglWorkspace]:
        """List workspaces for given user.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-workspaces)

        Args:
            since: Optional argument to filter any workspace after the timestamp.
            refresh: Whether to use cache or not.

        Raises:
            DateTimeError: If the since argument is after the current time.

        Returns:
            A list of workspaces or empty if there are None assocciated with the user.
        """
        if since is not None:
            since = self._validate_collect_since(since)

        if self.cache and not refresh:
            return list((await self._collect_cache(since)).fetchall())

        body = {"since": since} if since else None

        response = await self.request(
            "me/workspaces",
            body=body,
            refresh=refresh,
        )

        return cast("list[TogglWorkspace]", response)

    async def edit(
        self,
        workspace_id: TogglWorkspace | int,
        body: WorkspaceBody,
    ) -> TogglWorkspace:
        """Update a specific workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#put-update-workspace)

        Raises:
            HTTPStatusError: For anything thats not an *ok* status code.

        Returns:
            A workspace model with the supplied edits.
        """
        if isinstance(workspace_id, TogglWorkspace):
            workspace_id = workspace_id.id

        response = await self.request(
            f"workspaces/{workspace_id}",
            body=body.format("edit"),
            method=RequestMethod.PUT,
            refresh=True,
        )

        return cast("TogglWorkspace", response)

    async def tracker_constraints(
        self,
        workspace_id: TogglWorkspace | int,
    ) -> dict[str, bool]:
        """Get the time entry constraints for a given workspace.

        [Official Documentation](https://engineering.toggl.com/docs/api/workspaces#get-get-workspace-time-entry-constraints)

        Toggl premium feature.

        Examples:
            >>> await workspace_endpoint.get_workspace_constraints(24214214)
            {
                "description_present": True,
                "project_present": False,
                "tag_present": False",
                "task_present": False,
                "time_entry_constraints_enabled": True,
            }

        Args:
            workspace_id: Id of the workspace to retrieve constraints from.

        Returns:
            A dictionary of booleans containing the settings.
        """
        if isinstance(workspace_id, TogglWorkspace):
            workspace_id = workspace_id.id

        response = await self.request(
            f"workspaces/{workspace_id}/time_entry_constraints",
            raw=True,
            refresh=True,
        )
        return cast("dict[str, bool]", cast("Response", response).json())

    async def statistics(
        self,
        workspace_id: TogglWorkspace | int,
    ) -> WorkspaceStatistics:
        """Return workspace admins list, members count and groups count.

        [Official Documentation](https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/statistics)

        Args:
            workspace_id: Id of the workspace to fetch the statistics from.

        Returns:
            Dictionary containing relevant statistics.
                Refer to `WorkspaceStatistics` typed dict for reference.
        """
        if isinstance(workspace_id, TogglWorkspace):
            workspace_id = workspace_id.id

        response = await self.request(
            f"workspaces/{workspace_id}/statistics",
            refresh=True,
            raw=True,
        )

        return cast("WorkspaceStatistics", cast("Response", response).json())
