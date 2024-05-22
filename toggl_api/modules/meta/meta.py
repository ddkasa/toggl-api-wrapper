"""Metaclass for requesting and modiftying data from the Toggl API.

Classes:
    TogglRequest: Base class with basic functionality for all API requests.
"""

import enum
from abc import ABCMeta, abstractmethod
from types import MethodType
from typing import Any, Final, Optional

import httpx


class RequestMethod(enum.Enum):
    GET = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()
    DELETE = enum.auto()
    PATCH = enum.auto()


class TogglEndpoint(metaclass=ABCMeta):
    BASE_ENDPOINT: Final[str] = "https://api.track.toggl.com/api/v9/"
    OK_RESPONSE: Final[int] = 200
    HEADERS: Final[dict] = {"content-type": "application/json"}

    __slots__ = ("__client", "workspace_id", "headers")

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

    def method(self, method: RequestMethod) -> MethodType:
        match_dict = {
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
    ) -> dict | None:
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
            msg = f"Request failed with status code {response.status_code}: {response.text}"
            raise httpx.HTTPError(msg)

        try:
            return response.json()
        except ValueError:
            pass

        return None

    def body_creation(self, **kwargs) -> dict[str, Any]:
        """Generate basic headers for Toggl API request.

        Args:
            kwargs (dict): Misc header arguments for the request.

        Returns:
            dict: Basic headers for the Toggl API.
        """

        return {
            "workspace_id": self.workspace_id,
        }

    @property
    @abstractmethod
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT

    @property
    @abstractmethod
    def model(self):
        pass
