"""Metaclasses for requesting and modiftying data from the TOGGL API.

Classes:
    TogglRequest: Base class with basic functionality for all API requests.
    CacheTogglRequest: Adds caching functionality to TogglRequest.
"""

import enum
from abc import ABCMeta, abstractmethod
from types import MethodType
from typing import Final

import httpx


class RequestMethod(enum.Enum):
    GET = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()
    DELETE = enum.auto()
    PATCH = enum.auto()


class AuthenticationError(Exception):
    """No valid authentication provided."""


class TogglRequest(metaclass=ABCMeta):
    BASE_ENDPOINT: Final[str] = "https://api.track.toggl.com/api/v9/"
    OK_RESPONSE: Final[int] = 200

    __slots__ = ("__client", "workspace_id")

    def __init__(self, *, timeout: int = 20, **kwargs) -> None:
        self.workspace_id = kwargs.get("workspace_id")
        self.__client = httpx.Client(
            timeout=timeout,
            auth=self.authenticate(**kwargs),
            headers=self.headers(**kwargs),
        )

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
        url: str,
        method: RequestMethod = RequestMethod.GET,
        **kwargs,
    ) -> dict | None:
        response = self.method(method)(url)

        if response.status_code != self.OK_RESPONSE:
            # TODO: Toggl API return code lookup.
            msg = f"Request failed with status code {response.status_code}"
            raise httpx.HTTPError(msg)

        if response.is_json:
            return response.json()

        return None

    def headers(self, **kwargs) -> dict[str, str]:
        """Generate authentication headers for the Toggl Tracker API.

        Args:
            kwargs (dict): Toggl API credentials & extras.

        Returns:
            dict: Authentication headers prefilled with provided kwargs.
        """

        headers = {
            "content-type": "application/json",
        }

        if self.workspace_id:
            headers["workspace_id"] = self.workspace_id

        return headers

    def authenticate(self, **kwargs) -> httpx.BasicAuth:
        """Generate authentication headers for the Toggl tracker API.

        Args:
            kwargs (dict): Toggl API credentials & extras.

        Returns:
            BasicAuth: Authentication headers prefilled with provided kwargs.

        Raises:
            AuthenticationError: If not enough authentication material was
                provided.
        """
        api_token = kwargs.get("api_token")
        if api_token:
            return httpx.BasicAuth(api_token, "api_token")

        email = kwargs.get("email")
        if not email:
            msg = "No email was provided!"
            raise AuthenticationError(msg)
        password = kwargs.get("password")
        if not password:
            msg = "No password was provided!"
            raise AuthenticationError(msg)

        return httpx.BasicAuth(email, password)

    @property
    @abstractmethod
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT
