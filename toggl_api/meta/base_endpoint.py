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
from abc import ABC
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, ClassVar, Final, Generic, TypeVar

import httpx
from httpx import BasicAuth, Client, HTTPStatusError, Request, Response, codes

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
        client: Httpx client that is used for making requests to the API.

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
    ENDPOINT: ClassVar[str]
    HEADERS: Final[dict] = {"content-type": "application/json"}
    MODEL: type[T] | None = None

    __slots__ = ("client", "re_raise", "retries", "workspace_id")

    def __init__(
        self,
        workspace_id: int | None,
        auth: BasicAuth,
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
        self.client = Client(
            base_url=self.BASE_ENDPOINT,
            timeout=timeout,
            auth=auth,
        )
        atexit.register(self.client.close)

    def method(self, method: RequestMethod) -> Callable:
        warnings.warn(
            "DEPRECATED: Use `httpx.Client.build_request` instead!",
            DeprecationWarning,
            stacklevel=2,
        )
        match_dict: dict[RequestMethod, Callable] = {
            RequestMethod.GET: self.client.get,
            RequestMethod.POST: self.client.post,
            RequestMethod.PUT: self.client.put,
            RequestMethod.DELETE: self.client.delete,
            RequestMethod.PATCH: self.client.patch,
        }
        return match_dict.get(method, self.client.get)

    def _request_handle_error(
        self,
        response: Response,
        body: dict | list | None,
        headers: dict | None,
        method: RequestMethod,
        parameters: str,
        *,
        raw: bool,
        retries: int,
    ) -> T | list[T] | Response | None:
        msg = "Request failed with status code %s: %s"
        log.error(msg, response.status_code, response.text)

        if not self.re_raise and codes.is_server_error(response.status_code) and retries:
            delay = random.randint(1, 5)
            retries -= 1
            log.error(
                ("Status code %s is a server error. Retrying request in %s seconds. There are %s retries left."),
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

        return response.raise_for_status()

    def _process_response(self, response: Response, *, raw: bool) -> T | list[T] | Response | None:
        try:
            data = response if raw else response.json()
        except ValueError:
            return None

        if self.MODEL is None or raw:
            return data

        if isinstance(data, list):
            data = self.process_models(data)
        elif isinstance(data, dict):
            data = self.MODEL.from_kwargs(**data)

        return data  # type: ignore[return-value]

    def _build_request(
        self,
        parameters: str,
        headers: dict | None,
        body: dict | list | None,
        method: RequestMethod,
    ) -> Request:
        url = self.BASE_ENDPOINT + self.endpoint + parameters
        headers = headers or self.HEADERS

        requires_body = method not in {RequestMethod.DELETE, RequestMethod.GET}
        return self.client.build_request(
            method.name.lower(),
            url,
            headers=headers,
            json=body if requires_body else None,
        )

    def request(
        self,
        parameters: str,
        headers: dict | None = None,
        body: dict | list | None = None,
        method: RequestMethod = RequestMethod.GET,
        *,
        raw: bool = False,
        retries: int | None = None,
    ) -> T | list[T] | Response | None:
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

        request = self._build_request(parameters, headers, body, method)
        response = self.client.send(request)

        if codes.is_error(response.status_code):
            return self._request_handle_error(
                response,
                body,
                headers,
                method,
                parameters,
                raw=raw,
                retries=retries,
            )

        return self._process_response(response, raw=raw)

    @classmethod
    def process_models(cls, data: list[dict[str, Any]]) -> list[T]:
        assert cls.MODEL is not None
        return [cls.MODEL.from_kwargs(**mdl) for mdl in data]

    @property
    def model(self) -> type[T] | None:
        warnings.warn(
            "DEPRECATED: Use 'Endpoint.MODEL' ClassVar instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.MODEL

    @property
    def endpoint(self) -> str:
        warnings.warn(
            "DEPRECATED: Use 'Endpoint.BASE_ENDPOINT' ClassVar instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.BASE_ENDPOINT

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
