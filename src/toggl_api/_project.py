from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Final, Literal, cast

from httpx import Client, HTTPStatusError, Timeout, codes

from toggl_api._exceptions import NamingError
from toggl_api.meta.cache import Comparison, TogglQuery
from toggl_api.utility import format_iso, get_timestamp

from .meta import BaseBody, RequestMethod, TogglCachedEndpoint
from .models import TogglProject

if TYPE_CHECKING:
    from datetime import date

    from httpx import BasicAuth

    from toggl_api.meta.cache import TogglCache

    from .models import TogglWorkspace

log = logging.getLogger("toggl-api-wrapper.endpoint")


@dataclass
class ProjectBody(BaseBody):
    """JSON body dataclass for PUT, POST & PATCH requests."""

    name: str | None = field(default=None)
    """Name of the project. Defaults to None. Will be required if its a POST request."""

    active: bool | Literal["both"] = field(default=True)
    """Whether the project is archived or active.
    The literal 'both' is used for querying."""
    is_private: bool | None = field(
        default=True,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Whether the project is private or not. Defaults to True."""

    client_id: int | None = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    client_name: str | None = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Client name if client_id is not set. Defaults to None. If client_id is
    set the client_name will be ignored."""

    color: str | None = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Color of the project. Refer to [BASIC_COLORS][toggl_api.ProjectEndpoint.BASIC_COLORS]
    for accepted colors for non-premium users."""

    start_date: date | None = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Date to set the start of a project. If not set or start date is after
    the end date the end date will be ignored."""

    end_date: date | None = field(
        default=None,
        metadata={"endpoints": frozenset(("edit", "add"))},
    )
    """Date to set the end of the project. If not set or start date is after
    the end date the end date will be ignored."""

    since: date | int | None = field(
        default=None,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Timestamp for querying for projects with the 'collect' endpoint.
    Retrieve projects created/modified/deleted since this date using UNIX timestamp.
    *If using local cache deleted projects are not present.*
    """

    user_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific projects with assocciated users. API only."""

    client_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific projects with assocciated clients."""

    group_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific projects with assocciated groups. API only"""

    statuses: list[TogglProject.Status] = field(
        default_factory=list,
        metadata={"endpoints": frozenset(("collect",))},
    )
    """Query for specific statuses when using the collect endpoint.
    Deleted status only works with the remote API.
    """

    def _format_collect(self, body: dict[str, Any]) -> None:
        if self.since:
            body["since"] = get_timestamp(self.since)
        if self.user_ids:
            body["user_ids"] = self.user_ids
        if self.client_ids:
            body["client_ids"] = self.client_ids
        if self.group_ids:
            body["group_ids"] = self.group_ids
        if self.statuses:
            body["statuses"] = [s.name.lower() for s in self.statuses]

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Format the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            endpoint: Name of the endpoint for filtering purposes.
            body: Additional arguments for the body.

        Returns:
            dict[str, Any]: JSON compatible formatted body.
        """
        body.update(
            {
                "active": self.active,
                "is_private": self.is_private,
            },
        )
        if self.name:
            body["name"] = self.name
        if self.client_id:
            body["client_id"] = self.client_id
        elif self.client_name:
            body["client_name"] = self.client_name

        if self.color:
            color = ProjectEndpoint.get_color(self.color) if self.color in ProjectEndpoint.BASIC_COLORS else self.color
            body["color"] = color

        if self.start_date and self._verify_endpoint_parameter(
            "start_date",
            endpoint,
        ):
            body["start_date"] = format_iso(self.start_date)
        if self.end_date and self._verify_endpoint_parameter(
            "end_date",
            endpoint,
        ):
            if self.start_date and self.end_date < self.start_date:
                log.warning(
                    "End date is before the start date. Ignoring end date...",
                )
            else:
                body["end_date"] = format_iso(self.end_date)

        if endpoint == "collect":
            self._format_collect(body)

        return body


class ProjectEndpoint(TogglCachedEndpoint[TogglProject]):
    """Specific endpoints for retrieving and modifying projects.

    [Official Documentation](https://engineering.toggl.com/docs/api/projects)

    Examples:
        >>> from toggl_api.utility import get_authentication, retrieve_workspace_id
        >>> from toggl_api import JSONCache
        >>> project_endpoint = ProjectEndpoint(retrieve_workspace_id(), get_authentication(), JSONCache(...))
        >>> project_endpoint.get(213141424)
        TogglProject(213141424, "Amaryllis", ...)

        >>> project_endpoint.delete(213141424)
        None

    Params:
        workspace_id: The workspace the projects belong to.
        auth: Basic authentication with an api token or username/password combo.
        cache: Cache to push the projects to.
        client: Optional client to be passed to be used for requests. Useful
            when a global client is used and needs to be recycled.
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
        cache: TogglCache[TogglProject] | None = None,
        *,
        client: Client | None = None,
        timeout: Timeout | int = 10,
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
    def status_to_query(status: TogglProject.Status) -> list[TogglQuery[Any]]:
        """Create a list of queries depending on the desired project status.

        Args:
            status: What is the status you are querying for?

        Raises:
            NotImplementedError: Active & Deleted Statuses are currently not
                supported for local querying.

        Returns:
            A list of query parameters for the desired status.
        """
        if status == TogglProject.Status.ARCHIVED:
            return [TogglQuery("active", value=False)]

        now = datetime.now(timezone.utc)
        if status == TogglProject.Status.UPCOMING:
            return [TogglQuery("start_date", now, Comparison.LESS_THEN)]

        if status == TogglProject.Status.ENDED:
            return [TogglQuery("end_date", now, Comparison.GREATER_THEN)]

        msg = f"{status} status is not supported by local cache queries!"
        raise NotImplementedError(msg)

    def _collect_cache(self, body: ProjectBody | None) -> list[TogglProject]:
        if body:
            queries: list[TogglQuery[Any]] = []
            if isinstance(body.active, bool):
                queries.append(
                    TogglQuery("active", body.active, Comparison.EQUAL),
                )
            if body.since:
                queries.append(
                    TogglQuery(
                        "timestamp",
                        body.since,
                        Comparison.GREATER_THEN_OR_EQUAL,
                    ),
                )
            if body.client_ids:
                queries.append(TogglQuery("client", body.client_ids))
            if body.statuses:
                for status in body.statuses:
                    queries += self.status_to_query(status)

            return list(self.query(*queries))

        return list(self.load_cache())

    def collect(
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
        if not refresh:
            return self._collect_cache(body)

        return cast(
            "list[TogglProject]",
            self.request(
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
            ),
        )

    def get(
        self,
        project_id: int | TogglProject,
        *,
        refresh: bool = False,
    ) -> TogglProject | None:
        """Request a project based on its id.

        [Official Documentation](https://engineering.toggl.com/docs/api/projects#get-workspaceproject)

        Examples:
            >>> project_endpoint.get(213141424)
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
            return self.cache.find({"id": project_id})

        try:
            response = self.request(
                f"{self.endpoint}/{project_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                log.warning("Project with id %s was not found!", project_id)
                return None
            raise

        return cast("TogglProject", response) or None

    def delete(self, project: TogglProject | int) -> None:
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
            self.request(
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
            proj = self.cache.find({"id": project})
            if not isinstance(proj, TogglProject):
                return
            project = proj

        self.cache.delete(project)
        self.cache.commit()

    def edit(
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

        return cast(
            "TogglProject",
            self.request(
                f"{self.endpoint}/{project}",
                method=RequestMethod.PUT,
                body=body.format("edit", workspace_id=self.workspace_id),
                refresh=True,
            ),
        )

    def add(self, body: ProjectBody) -> TogglProject:
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
            NamingError: If the new project name is invalid.

        Returns:
            The newly created project.
        """
        if body.name is None:
            msg = "Name must be set in order to create a project!"
            raise NamingError(msg)

        return cast(
            "TogglProject",
            self.request(
                self.endpoint,
                method=RequestMethod.POST,
                body=body.format("add", workspace_id=self.workspace_id),
                refresh=True,
            ),
        )

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
