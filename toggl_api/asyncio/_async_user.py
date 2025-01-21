from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from httpx import Response

from ._async_endpoint import TogglAsyncEndpoint

if TYPE_CHECKING:
    from httpx import BasicAuth


log = logging.getLogger("toggl-api-wrapper.endpoint")


class AsyncUserEndpoint(TogglAsyncEndpoint):
    """Endpoint for retrieving user data.

    The synchronous sibling [UserEndpoint][toggl_api.UserEndpoint] has access to static
    method for verifying authentication.

    [Official Documentation](https://engineering.toggl.com/docs/api/me)

    Params:
        auth: Authentication for the client.
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
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(auth, timeout=timeout, re_raise=re_raise, retries=retries)

    async def get_details(self) -> dict[str, Any]:
        """Returns details for the current user.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-me)

        Raises:
            HTTPStatusError: If the request is not a successful status code.

        Returns:
            User details in a dictionary.
        """
        request = await self.request("me", raw=True)
        return cast(Response, request).json()
