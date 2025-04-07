from __future__ import annotations

import asyncio
import logging
import random
from abc import ABC
from collections.abc import Coroutine
from datetime import timedelta
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, ClassVar, Final, Generic, TypeVar, cast

from httpx import (
    URL,
    AsyncClient,
    BasicAuth,
    Headers,
    HTTPStatusError,
    Request,
    Response,
    Timeout,
    codes,
)

from toggl_api._exceptions import NoCacheAssignedError
from toggl_api.meta import RequestMethod
from toggl_api.models import TogglClass

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ._async_sqlite_cache import AsyncSqliteCache

log = logging.getLogger("toggl-api-wrapper.endpoint")

T = TypeVar("T", bound=TogglClass)


class TogglAsyncEndpoint(ABC, Generic[T]):
    """Base class with basic functionality for all async API requests.

    Attributes:
        BASE_ENDPOINT: Base URL of the Toggl API.
        HEADERS: Default headers that the API requires for most endpoints.
        client: Async httpx client that is used for making requests to the API.

    Params:
        auth: Authentication for the client.
        client: Optional async client to be passed to be used for requests.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    BASE_ENDPOINT: ClassVar[URL] = URL("https://api.track.toggl.com/api/v9/")
    HEADERS: Final[Headers] = Headers({"content-type": "application/json"})
    MODEL: type[T] | None = None

    def __init__(
        self,
        auth: BasicAuth,
        *,
        client: AsyncClient | None = None,
        timeout: Timeout | int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        self.client = client = client or AsyncClient()
        client.auth = auth
        client.base_url = self.BASE_ENDPOINT
        client.timeout = timeout if isinstance(timeout, Timeout) else Timeout(timeout)

        self.re_raise = re_raise
        self.retries = max(0, retries)

    async def _request_handle_error(
        self,
        response: Response,
        body: dict[str, Any] | list[dict[str, Any]] | None,
        headers: Headers | None,
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
            await asyncio.sleep(delay)
            return await TogglAsyncEndpoint.request(
                self,
                parameters=parameters,
                headers=headers,
                body=body,
                method=method,
                raw=raw,
                retries=retries,
            )

        return response.raise_for_status()

    async def _process_response(
        self,
        response: Response,
        *,
        raw: bool,
    ) -> T | list[T] | Response | None:
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

        return data

    async def _build_request(
        self,
        parameters: str,
        headers: Headers | None,
        body: dict[str, Any] | list[dict[str, Any]] | None,
        method: RequestMethod,
    ) -> Request:
        url = self.BASE_ENDPOINT.join(parameters)
        headers = headers or self.HEADERS

        requires_body = method not in {RequestMethod.DELETE, RequestMethod.GET}
        return self.client.build_request(
            method.name.lower(),
            url,
            headers=headers,
            json=body if requires_body else None,
        )

    async def request(
        self,
        parameters: str,
        headers: Headers | None = None,
        body: dict[str, Any] | list[dict[str, Any]] | None = None,
        method: RequestMethod = RequestMethod.GET,
        *,
        raw: bool = False,
        retries: int | None = None,
    ) -> T | list[T] | Response | None:
        if retries is None:
            retries = self.retries

        request = await self._build_request(parameters, headers, body, method)
        response = await self.client.send(request)

        if codes.is_error(response.status_code):
            return await self._request_handle_error(
                response,
                body,
                headers,
                method,
                parameters,
                raw=raw,
                retries=retries,
            )

        return await self._process_response(response, raw=raw)

    @classmethod
    def process_models(cls, data: list[dict[str, Any]]) -> list[T]:
        from_kwargs = cast("type[T]", cls.MODEL).from_kwargs
        return [from_kwargs(**mdl) for mdl in data]

    @staticmethod
    async def api_status() -> bool:
        """Verify that the Toggl API is up.

        Returns:
            `True` if the API is up.
        """
        try:
            request = await AsyncClient().get(
                "https://api.track.toggl.com/api/v9/status",
            )
            result = request.json()
        except (HTTPStatusError, JSONDecodeError):
            log.critical("Failed to get a response from the Toggl API!")
            log.exception("%s")
            return False

        return bool(result) and result.get("status") == "OK"


_T = TypeVar("_T", bound=Coroutine[Any, Any, Any])


class TogglAsyncCachedEndpoint(TogglAsyncEndpoint[T]):
    """Abstract cached endpoint for requesting toggl API data to disk.

    See parent endpoint for more details.

    Params:
        auth: Authentication for the client.
        cache: Cache object for caching toggl API data to disk.
            AsyncSqlitecache only available for now.
        client: Optional async client to be passed to be used for requests.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.

    Attributes:
        cache: Cache object the endpoint will use for storing models. Assigns
            itself as the parent automatically.
        client: Async httpx client that is used for making requests to the API.

    Methods:
        request: Overriden method that implements the cache into the request chain.
        load_cache: Method for loading cache into memory.
        save_cache: Method for saving cache to disk. Ignored if expiry is set
            to 0 seconds.
    """

    __slots__ = ("_cache",)

    def __init__(
        self,
        auth: BasicAuth,
        cache: AsyncSqliteCache[T] | None = None,
        *,
        client: AsyncClient | None = None,
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(
            auth=auth,
            client=client,
            timeout=timeout,
            re_raise=re_raise,
            retries=retries,
        )
        self.cache = cache

        self.__tasks: set[asyncio.Task[Any]] = set()

    async def request(  # type: ignore[override]
        self,
        parameters: str,
        headers: Headers | None = None,
        body: dict[str, Any] | list[Any] | None = None,
        method: RequestMethod = RequestMethod.GET,
        *,
        refresh: bool = False,
        raw: bool = False,
    ) -> T | list[T] | Response | None:
        """Overridden request method with builtin cache.

        Args:
            parameters: Request parameters with the endpoint excluded.
            headers: Request headers. Custom headers can be added here.
            body: Request body for GET, POST, PUT, PATCH requests.
                Defaults to None.
            method: Request method. Defaults to GET.
            refresh: Whether to refresh the cache or not. Defaults to False.
            raw (bool): Whether to use the raw data. Defaults to False.

        Raises:
            HTTPStatusError: If the request is not a success.

        Returns:
            Toggl API response data processed into TogglClass objects or not
                depending on arguments.
        """
        data = await self.load_cache() if self.cache and self.MODEL is not None else None
        if data and not refresh:
            log.info(
                "Loading request %s%s data from cache.",
                self.BASE_ENDPOINT,
                parameters,
                extra={"body": body, "headers": headers, "method": method},
            )
            return cast("list[T]", data)

        response = await super().request(
            parameters,
            method=method,
            headers=headers,
            body=body,
            raw=raw,
        )
        if isinstance(response, Response):
            return response

        if response is None or method == RequestMethod.DELETE:
            return None

        if self.cache and self.MODEL is not None:
            await self.save_cache(response, method)

        return response

    async def load_cache(self) -> Iterable[T]:
        """Direct loading method for retrieving all models from cache.

        Raises:
            NoCacheAssignedError: If no cache is assigned to the endpoint.

        Returns:
            Previously cached objects.
        """
        if self.cache is None:
            raise NoCacheAssignedError

        return await self.cache.load()

    async def save_cache(
        self,
        response: list[T] | T,
        method: RequestMethod,
    ) -> None:
        """Save all provided models to cache.

        Args:
            response: A list of values or single value to save.
            method: To method to use when updating the cache.

        Raises:
            NoCacheAssignedError: If no cache is assigned to the endpoint.
        """
        if self.cache is None:
            raise NoCacheAssignedError
        if isinstance(self.cache.expire_after, timedelta) and not self.cache.expire_after.total_seconds():
            log.debug(
                "Cache is set to immediately expire!",
                extra={"expiry": self.cache.expire_after},
            )
            return
        await self.cache.save(response, method)

    async def _create_task(self, coro: _T, name: str) -> asyncio.Task[_T]:
        """Create an async task with a strong reference.

        Args:
            coro: The coroutine to create a task for.
            name: What to name the task for reference.

        Returns:
            Task that was added to the tasks list.
        """
        task = asyncio.create_task(coro, name=name)
        self.__tasks.add(task)
        task.add_done_callback(self.__tasks.remove)
        return task

    @property
    def cache(self) -> AsyncSqliteCache[T] | None:
        return self._cache

    @cache.setter
    def cache(self, value: AsyncSqliteCache[T] | None) -> None:
        self._cache = value
        if self.cache and self.cache._parent is not self:  # noqa: SLF001
            self.cache.parent = self
