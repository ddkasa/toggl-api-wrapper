from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, cast

import httpx
from httpx import HTTPStatusError, Response, codes

from .meta import TogglCachedEndpoint, TogglEndpoint
from .models import TogglTracker

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api.models.models import TogglWorkspace

    from .meta import TogglCache

log = logging.getLogger("toggl-api-wrapper.endpoint")


class UserEndpoint(TogglCachedEndpoint[TogglTracker]):
    """Endpoint for retrieving and fetching trackers with GET requests.

    See the [TrackerEndpoint][toggl_api.TrackerEndpoint] for modifying trackers.

    [Official Documentation](https://engineering.toggl.com/docs/api/me)

    Params:
        workspace_id: The workspace the Toggl trackers belong to.
        auth: Authentication for the client.
        cache: Cache object where trackers are stored.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    MODEL = TogglTracker

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: TogglCache[TogglTracker] | None = None,
        *,
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(0, auth, cache, timeout=timeout, re_raise=re_raise, retries=retries)
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    def get(
        self,
        tracker_id: int | TogglTracker,
        *,
        refresh: bool = False,
    ) -> TogglTracker | None:
        """Get a single tracker by ID.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#get-get-a-time-entry-by-id)

        Args:
            tracker_id: ID of the tracker to get.
            refresh: Whether to refresh the cache or not.

        Raises:
            HTTPStatusError: If anything thats not a *ok* or *404* status code
                is returned.

        Returns:
            TogglTracker object or None if not found.
        """
        if isinstance(tracker_id, TogglTracker):
            tracker_id = tracker_id.id

        if self.cache and not refresh:
            return self.cache.find({"id": tracker_id})

        try:
            response = self.request(
                f"/time_entries/{tracker_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                log.warning("Tracker with id %s does not exist!", tracker_id)
                return None
            raise

        return cast(TogglTracker, response)

    @staticmethod
    def verify_authentication(auth: BasicAuth) -> bool:
        """Check if user is correctly authenticated with the Toggl API.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-logged)

        Examples:
            >>> UserEndpoint.verify_authentication(auth)
            True

            >>> auth = generate_authentication()
            >>> UserEndpoint.verify_authentication(auth)
            True

        Args:
            auth: Basic authentication object either created manually or one
                of the provided authentication utilities.

        Raises:
            HTTPStatusError: If anything that is error status code that is not
                a FORBIDDEN code.

        Returns:
            True if successfully verified authentication else False.
        """
        try:
            httpx.get(TogglEndpoint.BASE_ENDPOINT + "me/logged", auth=auth).raise_for_status()
        except HTTPStatusError as err:
            log.critical("Failed to verify authentication!")
            log.exception("%s")
            if err.response.status_code != codes.FORBIDDEN:
                raise

            return False

        return True

    def get_details(self) -> dict[str, Any]:
        """Returns details for the current user.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-me)

        Raises:
            HTTPStatusError: If the request is not a successful status code.

        Returns:
            User details in a raw dictionary.
        """
        return cast(Response, TogglEndpoint.request(self, "", raw=True)).json()

