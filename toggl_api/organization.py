from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from httpx import HTTPStatusError, codes

from toggl_api.meta import RequestMethod

from .meta import TogglCachedEndpoint
from .models import TogglOrganization, TogglWorkspace

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api.meta.cache.base_cache import TogglCache


log = logging.getLogger("toggl-api-wrapper.endpoint")


class OrganizationEndpoint(TogglCachedEndpoint):
    """Endpoint to do with handling organization specific details.

    [Official Documentation](https://engineering.toggl.com/docs/api/organizations)
    """

    def __init__(self, auth: BasicAuth, cache: TogglCache, *, timeout: int = 20, **kwargs) -> None:
        super().__init__(0, auth, cache, timeout=timeout, **kwargs)

    def get(
        self,
        organization: TogglOrganization | int,
        *,
        refresh: bool = False,
    ) -> TogglOrganization | None:
        """Creates a new organization with a single workspace and assigns
        current user as the organization owner

        [Official Documentation](https://engineering.toggl.com/docs/api/organizations#get-organization-data)

        Args:
            organization: Organization to retrieve.
            refresh: Whether to ignore cache completely.

        Raises:
            HTTPStatusError: If any error except a '404' was received.

        Returns:
            TogglOrganization | None: Organization object that was retrieve or
                None if not found.
        """

        if isinstance(organization, TogglOrganization):
            organization = organization.id

        if not refresh:
            return self.cache.find_entry({"id": organization})  # type: ignore[return-value]

        try:
            response = self.request(f"organizations/{organization}", refresh=refresh)
        except HTTPStatusError as err:
            if err.response.status_code in {codes.NOT_FOUND, codes.FORBIDDEN}:
                log.warning(err)
                return None
            raise

        return response

    def add(self, name: str, workspace_name: str = "Default-Workspace") -> TogglOrganization:
        """Creates a new organization with a single workspace and assigns
        current user as the organization owner

        [Official Documentation](https://engineering.toggl.com/docs/api/organizations#post-creates-a-new-organization)

        Examples:
            >>> org = organization_endpoint.add("New-Workspace")
            >>> org.name
            "New-Workspace"

        Args:
            name: Name of the new orgnization.
            workspace_name: Name of the default workspace in the organization.
                No space characters allowed.

        Raises:
            ValueError: If any of the names are invalid or the long length.

        Returns:
            TogglOrganization: The newly created organization.
        """

        TogglOrganization.validate_name(name)
        TogglWorkspace.validate_name(workspace_name)

        return self.request(
            "organizations",
            body={"name": name, "workspace_name": workspace_name},
            method=RequestMethod.POST,
            refresh=True,
        )

    @property
    def model(self) -> type[TogglOrganization]:
        return TogglOrganization

    @property
    def endpoint(self) -> str:
        return ""
