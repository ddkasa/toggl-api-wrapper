"""Metaclass for requesting and modiftying data from the Toggl API.

Classes:
    TogglRequest: Base class with basic functionality for all API requests.
"""

from __future__ import annotations

import atexit
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Final, Optional

import httpx

from toggl_api.modules.models.models import TogglClass

from .enums import RequestMethod

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger("toggl_api")


class TogglEndpoint(ABC):
    """Base class with basic functionality for all API requests."""

    OK_RESPONSE: Final[int] = 200
    NOT_FOUND: Final[int] = 404
    SERVER_ERROR: Final[int] = 5

    BASE_ENDPOINT: Final[str] = "https://api.track.toggl.com/api/v9/"
    HEADERS: Final[dict] = {"content-type": "application/json"}

    __slots__ = ("__client", "workspace_id")

    def __init__(
        self,
        workspace_id: int,
        auth: httpx.BasicAuth,
        *,
        timeout: int = 20,
        **kwargs,
    ) -> None:
        self.workspace_id = workspace_id
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
        body: Optional[dict] = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> Optional[list[TogglClass] | TogglClass]:
        """Main request method which handles putting together the final API
        request.

        Args:
            parameters (str): Request parameters with the endpoint excluded.
                Will concate with the endpoint property.
            headers (dict, optional): Custom request headers. Defaults to
                class property if set to None.
            body (dict, optional): Request body JSON data for specifying info.
                Defaults to None. Only used with none-GET or DELETE requests.
            method (RequestMethod): Request method to select. Defaults to GET.

        Returns:
            dict | None: Response data or None if request does not return any
                data.
        """

        url = self.endpoint + parameters
        headers = headers or self.HEADERS

        if body and method not in {RequestMethod.DELETE, RequestMethod.GET}:
            response = self.method(method)(url, headers=headers, json=body)
        else:
            response = self.method(method)(url, headers=headers)

        if response.status_code != self.OK_RESPONSE:
            # TODO: Toggl API return code lookup.
            msg = "Request failed with status code %s: %s"
            log.error(msg, response.status_code, response.text)
            if response.status_code % 100 == self.SERVER_ERROR:
                delay = random.randint(1, 5)  # noqa: S311
                log.info("Status code is a server error. Retrying request in %s seconds", delay)
                time.sleep(delay)
                return self.request(parameters, headers, body, method)

            response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            return None

        if isinstance(data, list):
            data = self.process_models(data)
        elif isinstance(data, dict):
            data = self.model.from_kwargs(**data)

        return data

    def process_models(
        self,
        data: list[dict[str, Any]],
    ) -> list[TogglClass]:
        return [self.model.from_kwargs(**mdl) for mdl in data]

    @property
    @abstractmethod
    def endpoint(self) -> str:
        pass

    @property
    @abstractmethod
    def model(self) -> type[TogglClass]:
        return TogglClass
