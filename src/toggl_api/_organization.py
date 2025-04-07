from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from httpx import Client, HTTPStatusError, Timeout, codes

from toggl_api.meta import RequestMethod

from .meta import TogglCachedEndpoint
from .models import TogglOrganization, TogglWorkspace

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api.meta.cache import TogglCache


log = logging.getLogger("toggl-api-wrapper.endpoint")


class OrganizationEndpoint(TogglCachedEndpoint[TogglOrganization]):
    """Endpoint to do with handling organization specific details.

    [Official Documentation](https://engineering.toggl.com/docs/api/organizations)

    Examples:
        >>> org_endpoint = OrganizationEndpoint(BasicAuth(...), SqliteCache(...))

    Params:
        auth: Authentication for the client.
        cache: Cache object where the organization models are stored.
        client: Optional client to be passed to be used for requests. Useful
            when a global client is used and needs to be recycled.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    MODEL = TogglOrganization

    def __init__(
        self,
        auth: BasicAuth,
        cache: TogglCache[TogglOrganization] | None = None,
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

    def get(
        self,
        organization: TogglOrganization | int,
        *,
        refresh: bool = False,
    ) -> TogglOrganization | None:
        """Create a new organization with a single workspace and assigns
        current user as the organization owner.

        [Official Documentation](https://engineering.toggl.com/docs/api/organizations#get-organization-data)

        Args:
            organization: Organization to retrieve.
            refresh: Whether to ignore cache completely.

        Raises:
            HTTPStatusError: If any error except a '404' was received.

        Returns:
            Organization object that was retrieve or None if not found.
        """  # noqa: D205
        if isinstance(organization, TogglOrganization):
            organization = organization.id

        if self.cache and not refresh:
            return self.cache.find({"id": organization})

        try:
            response = self.request(
                f"organizations/{organization}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code in {
                codes.NOT_FOUND,
                codes.FORBIDDEN,
            }:
                log.warning(err)
                return None
            raise

        return cast("TogglOrganization", response)

    def add(
        self,
        name: str,
        workspace_name: str = "Default-Workspace",
    ) -> TogglOrganization:
        """Create a new organization with a single workspace.

        Assigns current user as the organization owner.

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
            NamingError: If any of the names are invalid or the wrong length.
            HTTPStatusError: If the request is not a success.

        Returns:
            The newly created organization.
        """
        TogglOrganization.validate_name(name)
        TogglWorkspace.validate_name(workspace_name)

        return cast(
            "TogglOrganization",
            self.request(
                "organizations",
                body={"name": name, "workspace_name": workspace_name},
                method=RequestMethod.POST,
                refresh=True,
            ),
        )

    def edit(
        self,
        organization: TogglOrganization | int,
        name: str,
    ) -> TogglOrganization:
        """Update an existing organization.

        [Official Documentation](https://engineering.toggl.com/docs/api/organizations#put-updates-an-existing-organization)

        Args:
            organization: The id of the organization to edit.
            name: What name to change the org to.

        Raises:
            NamingError: If the new name is invalid.
            HTTPStatusError: If the request is not a success.

        Returns:
            The newly edited organization.
        """
        TogglOrganization.validate_name(name)

        if isinstance(organization, TogglOrganization):
            organization = organization.id

        self.request(
            f"organizations/{organization}",
            body={"name": name},
            refresh=True,
            method=RequestMethod.PUT,
        )

        edit = TogglOrganization(organization, name)
        if self.cache:
            self.cache.update(edit)
            self.cache.commit()

        return edit

    def collect(self, *, refresh: bool = False) -> list[TogglOrganization]:
        """Get all organizations a given user is part of.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-organizations-that-a-user-is-part-of)

        Args:
            refresh: Whether to use cache or not.

        Raises:
            HTTPStatusError: If the request is not a success.

        Returns:
            A list of organization objects or empty if none found.
        """
        return cast(
            "list[TogglOrganization]",
            self.request("me/organizations", refresh=refresh),
        )

    def delete(self, organization: TogglOrganization | int) -> None:
        """Leave organization effectively deleting user account in org.

        Deletes organization if it is last user.

        Deletion might not be instant on the API end and might take a few
        seconds to propogate, so the object might appear in the 'get' or
        'collect' method.

        [Official Documentation](https://engineering.toggl.com/docs/api/organizations#delete-leaves-organization)

        Args:
            organization: Organization to delete.

        Raises:
            HTTPStatusError: If the response status_code is not '200' or '404'.
        """
        org_id = organization if isinstance(organization, int) else organization.id
        try:
            self.request(
                f"organizations/{org_id}/users/leave",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if self.re_raise or err.response.status_code != codes.NOT_FOUND:
                raise
            log.exception("%s")
            log.warning(
                "Organization with id %s was either already deleted or did not exist in the first place!",
                org_id,
            )
        if self.cache is None:
            return

        if isinstance(organization, int):
            org = self.cache.find({"id": organization})
            if not isinstance(org, TogglOrganization):
                return
            organization = org

        self.cache.delete(organization)
        self.cache.commit()

    @property
    def endpoint(self) -> str:
        return ""
