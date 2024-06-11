"""Metaclass for requesting and modiftying data from the Toggl API.

Classes:
    TogglRequest: Base class with basic functionality for all API requests.
"""

import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from typing import Any, Final, Optional

import httpx

from toggl_api.modules.models.models import TogglClass

from .enums import RequestMethod

log = logging.getLogger("toggl_api")


class TogglEndpoint(metaclass=ABCMeta):
    """Base class with basic functionality for all API requests."""

    OK_RESPONSE: Final[int] = 200
    NOT_FOUND: Final[int] = 404

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
        self.__client = httpx.Client(timeout=timeout, auth=auth)

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
        headers = headers if headers else self.HEADERS

        if body and method not in (RequestMethod.DELETE, RequestMethod.GET):
            response = self.method(method)(url, headers=headers, json=body)
        else:
            response = self.method(method)(url, headers=headers)

        if response.status_code != self.OK_RESPONSE:
            # TODO: Toggl API return code lookup.
            # TODO: If a "already exists" 400 code is returned it should return the get or None.
            msg = "Request failed with status code %s: %s"
            log.error(msg, response.status_code, response.text)
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
        return self.BASE_ENDPOINT

    @property
    @abstractmethod
    def model(self) -> type[TogglClass]:
        return TogglClass
