from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from httpx import Client, HTTPStatusError, Response, Timeout, codes

from .meta import TogglEndpoint

if TYPE_CHECKING:
    from httpx import BasicAuth


log = logging.getLogger("toggl-api-wrapper.endpoint")


class UserEndpoint(TogglEndpoint[Any]):
    """Endpoint for retrieving user data.

    [Official Documentation](https://engineering.toggl.com/docs/api/me)

    Params:
        auth: Authentication for the client.
        client: Optional client to be passed to be used for requests. Useful
            when a global client is used and needs to be recycled.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    def __init__(
        self,
        auth: BasicAuth,
        *,
        client: Client | None = None,
        timeout: Timeout | int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(
            auth,
            client=client,
            timeout=timeout,
            re_raise=re_raise,
            retries=retries,
        )

    @staticmethod
    def verify_authentication(
        auth: BasicAuth,
        *,
        client: Client | None = None,
    ) -> bool:
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
            client: Optional client for making the requests with when using a
                singleton/global client.

        Raises:
            HTTPStatusError: If anything that is error status code that is not
                a FORBIDDEN code.

        Returns:
            True if successfully verified authentication else False.
        """
        client = client or Client()
        try:
            client.get(
                TogglEndpoint.BASE_ENDPOINT + "me/logged",
                auth=auth,
            ).raise_for_status()
        except HTTPStatusError as err:
            log.critical("Failed to verify authentication!")
            log.exception("%s")
            if err.response.status_code != codes.FORBIDDEN:
                raise

            return False

        return True

    def get_details(self) -> dict[str, Any]:
        """Return details for the current user.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-me)

        Raises:
            HTTPStatusError: If the request is not a successful status code.

        Returns:
            User details in a raw dictionary.
        """
        return cast(
            "dict[str, Any]",
            cast(
                "Response",
                self.request("me", raw=True),
            ).json(),
        )
