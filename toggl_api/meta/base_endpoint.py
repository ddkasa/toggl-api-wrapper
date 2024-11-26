"""Metaclass for requesting and modiftying data from the Toggl API.

Classes:
    TogglEndpoint: Base class with basic functionality for all API requests.
"""

from __future__ import annotations

import atexit
import logging
import random
import time
import warnings
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, ClassVar, Final, Generic, Optional, TypeVar

import httpx
from httpx import HTTPStatusError, codes

from toggl_api.models import TogglClass

from .enums import RequestMethod

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger("toggl-api-wrapper.endpoint")


T = TypeVar("T", bound=TogglClass)


class TogglEndpoint(ABC, Generic[T]):
    """Base class with basic functionality for all API requests.

    Attributes:
        BASE_ENDPOINT: Base URL of the Toggl API.
        HEADERS: Default headers that the API requires for most endpoints.

    Params:
        workspace_id: DEPRECATED and moved to child classes.
        auth: Authentication for the client.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    BASE_ENDPOINT: ClassVar[str] = "https://api.track.toggl.com/api/v9/"
    HEADERS: Final[dict] = {"content-type": "application/json"}

    __slots__ = ("__client", "re_raise", "retries", "workspace_id")

    def __init__(
        self,
        workspace_id: int | None,
        auth: httpx.BasicAuth,
        *,
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        if workspace_id:
            warnings.warn(
                "DEPRECATED: 'workspace_id' is being removed from the base Toggl endpoint!",
                DeprecationWarning,
                stacklevel=3,
            )

        self.workspace_id = workspace_id
        self.re_raise = re_raise
        self.retries = max(0, retries)

        # NOTE: USES BASE_ENDPOINT instead of endpoint property for base_url
        # as current httpx concatenation is causing appended slashes.
        self.__client = httpx.Client(
            base_url=self.BASE_ENDPOINT,
            timeout=timeout,
            auth=auth,
        )
        atexit.register(self.__client.close)

    def method(self, method: RequestMethod) -> Callable:
        match_dict: dict[RequestMethod, Callable] = {
            RequestMethod.GET: self.__client.get,
            RequestMethod.POST: self.__client.post,
            RequestMethod.PUT: self.__client.put,
            RequestMethod.DELETE: self.__client.delete,
            RequestMethod.PATCH: self.__client.patch,
        }
        return match_dict.get(method, self.__client.get)

    def request(
        self,
        parameters: str,
        headers: Optional[dict] = None,
        body: Optional[dict | list] = None,
        method: RequestMethod = RequestMethod.GET,
        *,
        raw: bool = False,
        retries: int | None = None,
    ) -> Any:
        """Main request method which handles putting together the final API
        request.

        Args:
            parameters (str): Request parameters with the endpoint excluded.
                Will concate with the endpoint property.
            headers (dict, optional): Custom request headers. Defaults to
                class property if set to None.
            body (dict | list, optional): Request body JSON data for specifying info.
                Defaults to None. Only used with none-GET or DELETE requests.
            method (RequestMethod): Request method to select. Defaults to GET.
            raw (bool): Whether to use the raw data. Defaults to False.
            retries (int): For recursive calls if the server fails multiple times.

        Raises:
            HTTPStatusError: If the request is not a success.

        Returns:
            Response data or None if request does not return any data.
        """
        if retries is None:
            retries = self.retries

        url = self.endpoint + parameters
        headers = headers or self.HEADERS

        if body and method not in {RequestMethod.DELETE, RequestMethod.GET}:
            response = self.method(method)(url, headers=headers, json=body)
        else:
            response = self.method(method)(url, headers=headers)

        if codes.is_error(response.status_code):
            msg = "Request failed with status code %s: %s"
            log.error(msg, response.status_code, response.text)

            if not self.re_raise and codes.is_server_error(response.status_code) and retries:
                delay = random.randint(1, 5)
                retries -= 1
                log.error(
                    (
                        "Status code %s is a server error. "
                        "Retrying request in %s seconds. "
                        "There are %s retries left."
                    ),
                    response.status_code,
                    delay,
                    retries,
                )
                # NOTE: According to https://engineering.toggl.com/docs/#generic-responses
                time.sleep(delay)
                return TogglEndpoint.request(
                    self,
                    parameters,
                    headers,
                    body,
                    method,
                    raw=raw,
                    retries=retries,
                )

            response.raise_for_status()

        try:
            data = response if raw else response.json()
        except ValueError:
            return None

        if self.model is None:
            return data

        if isinstance(data, list):
            data = self.process_models(data)
        elif isinstance(data, dict):
            data = self.model.from_kwargs(**data)

        return data

    def process_models(self, data: list[dict[str, Any]]) -> list[T]:
        return [self.model.from_kwargs(**mdl) for mdl in data]  # type: ignore[misc]

    @property
    @abstractmethod
    def endpoint(self) -> str: ...

    @property
    @abstractmethod
    def model(self) -> type[T]: ...

    @staticmethod
    def api_status() -> bool:
        """Method for verifying that the Toggl API is up."""
        try:
            result = httpx.get("https://api.track.toggl.com/api/v9/status").json()
        except (HTTPStatusError, JSONDecodeError):
            log.critical("Failed to get a response from the Toggl API!")
            log.exception("%s")
            return False

        return bool(result) and result.get("status") == "OK"
