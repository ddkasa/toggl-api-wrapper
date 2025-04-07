from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Final, cast

from httpx import AsyncClient, HTTPStatusError, codes
from sqlalchemy import Column, select
from sqlalchemy.ext.asyncio import AsyncSession

from toggl_api import TogglProject
from toggl_api._exceptions import NamingError
from toggl_api.meta import RequestMethod

from ._async_endpoint import TogglAsyncCachedEndpoint

if TYPE_CHECKING:
    from httpx import BasicAuth
    from sqlalchemy.engine import ScalarResult
    from sqlalchemy.sql.expression import ColumnElement, Select

    from toggl_api import TogglWorkspace
    from toggl_api._project import ProjectBody

    from ._async_sqlite_cache import AsyncSqliteCache


log = logging.getLogger("toggl-api-wrapper.endpoint")


class AsyncProjectEndpoint(TogglAsyncCachedEndpoint[TogglProject]):
    """Specific endpoints for retrieving and modifying projects.

    [Official Documentation](https://engineering.toggl.com/docs/api/projects)

    Examples:
        >>> from toggl_api.utility import get_authentication, retrieve_workspace_id
        >>> from toggl_api.asyncio import AsyncSqliteCache, ProjectEndpoint
        >>> project_endpoint = ProjectEndpoint(retrieve_workspace_id(), get_authentication(), AsyncSqliteCache(...))
        >>> await project_endpoint.get(213141424)
        TogglProject(213141424, "Amaryllis", ...)

        >>> await project_endpoint.delete(213141424)
        None

    Params:
        workspace_id: The workspace the projects belong to.
        auth: Basic authentication with an api token or username/password combo.
        cache: Cache to push the projects to.
        client: Optional async client to be passed to be used for requests.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.

    Attributes:
        BASIC_COLORS: Default colors that are available for non-premium users.
    """

    MODEL = TogglProject

    BASIC_COLORS: Final[dict[str, str]] = {
        "blue": "#0b83d9",
        "violet": "#9e5bd9",
        "pink": "#d94182",
        "orange": "#e36a00",
        "gold": "#bf7000",
        "green": "#2da608",
        "teal": "#06a893",
        "beige": "#c9806b",
        "dark-blue": "#465bb3",
        "purple": "#990099",
        "yellow": "#c7af14",
        "dark-green": "#566614",
        "red": "#d92b2b",
        "gray": "#525266",
    }
    """Basic colors available for projects in order of the API index."""

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: AsyncSqliteCache[TogglProject] | None = None,
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
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    @staticmethod
    def status_to_query(
        status: TogglProject.Status,
        statement: Select[Any],
    ) -> Select[Any]:
        """Create a list of queries depending on the desired project status.

        Args:
            status: What is the status you are querying for?
            statement: Base statement to add filters onto.

        Raises:
            NotImplementedError: Active & Deleted Statuses are currently not
                supported for local querying.

        Returns:
            A list of query parameters for the desired status.
        """
        if status == TogglProject.Status.ARCHIVED:
            return statement.filter(
                cast("ColumnElement[bool]", not TogglProject.active),
            )

        now = datetime.now(timezone.utc)
        if status == TogglProject.Status.UPCOMING:
            return statement.filter(
                cast("ColumnElement[bool]", TogglProject.start_date <= now),
            )

        if status == TogglProject.Status.ENDED:
            return statement.filter(
                cast(
                    "ColumnElement[bool]",
                    cast("date", TogglProject.end_date) > now,
                ),
            )

        msg = f"{status} status is not supported by local cache queries!"
        raise NotImplementedError(msg)

    async def _collect_cache(
        self,
        body: ProjectBody | None,
    ) -> ScalarResult[TogglProject]:
        statement = select(self.MODEL)
        if body:
            if isinstance(body.active, bool):
                statement = statement.filter(
                    cast(
                        "ColumnElement[bool]",
                        TogglProject.active == body.active,
                    ),
                )
            if body.since:
                statement = statement.filter(
                    cast(
                        "ColumnElement[bool]",
                        TogglProject.timestamp >= cast("datetime", body.since),
                    ),
                )
            if body.client_ids:
                statement = statement.filter(
                    cast(
                        "ColumnElement[bool]",
                        cast("Column[int]", TogglProject.client).in_(
                            body.client_ids,
                        ),
                    ),
                )
            if body.statuses:
                for status in body.statuses:
                    statement = self.status_to_query(status, statement)

        cache = cast("AsyncSqliteCache[TogglProject]", self.cache)
        async with AsyncSession(
            cache.database,
            expire_on_commit=False,
        ) as session:
            return (await session.execute(statement)).scalars()

    async def collect(
        self,
        body: ProjectBody | None = None,
        *,
        refresh: bool = False,
        sort_pinned: bool = False,
        only_me: bool = False,
        only_templates: bool = False,
    ) -> list[TogglProject]:
        """Return all cached or remote projects.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#get-workspaceprojects)

        Args:
            body: Optional body for adding query parameters for filtering projects.
            refresh: Whether to fetch from the remote API if true else using
                the local cache.
            sort_pinned: Whether to put pinned projects ontop of the results.
                Only works with the remote API at the moment.
            only_me: Only retrieve projects that are assigned to the current
                user assocciated with the authentication. API specific.
            only_templates: Retrieve template projects. API specific.

        Raises:
            HTTPStatusError: If any response that is not '200' code is returned.
            NotImplementedError: Deleted or Active status are used with a 'False'
                refresh argument.

        Returns:
            A list of projects or an empty list if None are found.
        """
        if self.cache and not refresh:
            return list(await self._collect_cache(body))

        response = await self.request(
            self.endpoint,
            body=body.format(
                "collect",
                workspace_id=self.workspace_id,
                sort_pinned=sort_pinned,
                only_me=only_me,
                only_templates=only_templates,
            )
            if body
            else {
                "sort_pinned": sort_pinned,
                "only_me": only_me,
                "only_templates": only_templates,
            },
            refresh=refresh,
        )

        return cast("list[TogglProject]", response)

    async def get(
        self,
        project_id: int | TogglProject,
        *,
        refresh: bool = False,
    ) -> TogglProject | None:
        """Request a project based on its id.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#get-workspaceproject)

        Examples:
            >>> await project_endpoint.get(213141424)
            TogglProject(213141424, "Amaryllis", ...)

        Args:
            project_id: TogglProject to retrieve. Either a model with the correct id or integer.
            refresh: Whether to check cache or not.

        Raises:
            HTTPStatusError: If any status code that is not '200' or a '404' is returned.

        Returns:
            A project model or None if nothing was found.
        """
        if isinstance(project_id, TogglProject):
            project_id = project_id.id

        if self.cache and not refresh:
            return await self.cache.find(project_id)

        try:
            response = await self.request(
                f"{self.endpoint}/{project_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                log.warning("Project with id %s was not found!", project_id)
                return None
            raise

        return cast("TogglProject", response) or None

    async def delete(self, project: TogglProject | int) -> None:
        """Delete a project based on its id.

        This endpoint always hits the external API in order to keep projects consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#delete-workspaceproject)

        Examples:
            >>> project_endpoint.delete(213141424)
            None

        Args:
            project: TogglProject to delete. Either an existing model or the integer id.

        Raises:
            HTTPStatusError: For anything that's not a '200' or '404' status code.
        """
        project_id = project if isinstance(project, int) else project.id
        try:
            await self.request(
                f"{self.endpoint}/{project_id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if self.re_raise or err.response.status_code != codes.NOT_FOUND:
                raise
            log.warning(
                "Project with id %s was either already deleted or did not exist in the first place!",
                project_id,
            )
        if self.cache is None:
            return
        if isinstance(project, int):
            proj = await self.cache.find(project)
            if not isinstance(proj, TogglProject):
                return
            project = proj

        await self.cache.delete(project)

    async def edit(
        self,
        project: TogglProject | int,
        body: ProjectBody,
    ) -> TogglProject:
        """Edit a project based on its id with the parameters provided in the body.

        This endpoint always hit the external API in order to keep projects consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#put-workspaceproject)

        Examples:
            >>> body = ProjectBody(name="Amaryllis")
            >>> project_endpoint.add(213141424, body)
            TogglProject(213141424, "Amaryllis", client=87695895, ...)

        Args:
            project: The existing project to edit. Either the model or the integer id.
            body: The body with the edited attributes.

        Raises:
            HTTPStatusError: For anything that's not a 'ok' status code.

        Returns:
            The project model with the provided modifications.
        """
        if isinstance(project, TogglProject):
            project = project.id

        response = await self.request(
            f"{self.endpoint}/{project}",
            method=RequestMethod.PUT,
            body=body.format("edit", workspace_id=self.workspace_id),
            refresh=True,
        )

        return cast("TogglProject", response)

    async def add(self, body: ProjectBody) -> TogglProject:
        """Create a new project based on the parameters provided in the body.

        This endpoint always hit the external API in order to keep projects consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#post-workspaceprojects)

        Examples:
            >>> body = ProjectBody(name="Zinnia", client_id=87695895)
            >>> project_endpoint.add(body)
            TogglProject(213141424, "Zinnia", client=87695895, ...)

        Args:
            body: The body with the new attributes of the project.

        Raises:
            HTTPStatusError: For anything that's not a 'ok' status code.
            NamingError: If the project name is invalid.

        Returns:
            The newly created project.
        """
        if body.name is None:
            msg = "Name must be set in order to create a project!"
            raise NamingError(msg)

        response = await self.request(
            self.endpoint,
            method=RequestMethod.POST,
            body=body.format("add", workspace_id=self.workspace_id),
            refresh=True,
        )

        return cast("TogglProject", response)

    @classmethod
    def get_color(cls, name: str) -> str:
        """Get a color by name. Defaults to gray.

        Args:
            name: The name of the color.

        Returns:
            Color in a hexcode.
        """
        return cls.BASIC_COLORS.get(name, "#525266")

    @classmethod
    def get_color_id(cls, color: str) -> int:
        """Get a color id by name.

        Args:
            color: Name of the desired color.

        Raises:
            IndexError: If the color name is not a standard color.

        Returns:
            Index of the provided color name.
        """
        colors = list(cls.BASIC_COLORS.values())
        return colors.index(color)

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/projects"
