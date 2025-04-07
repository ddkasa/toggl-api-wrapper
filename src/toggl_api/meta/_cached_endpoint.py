"""Module that deals with caching API data permanently to disk.

Classes:
    TogglCache: Abstract class for caching toggl API data to disk.
    JSONCache: Class for caching data to disk in JSON format.
    SqliteCache: Class for caching data to disk in sqlite format.
    TogglCachedEndpoint: Abstract class for caching and requesting toggl API
        data to disk.

"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypeVar, cast

from toggl_api._exceptions import NoCacheAssignedError
from toggl_api.models import TogglClass

from ._base_endpoint import TogglEndpoint
from ._enums import RequestMethod

if TYPE_CHECKING:
    from collections.abc import Iterable

    from httpx import BasicAuth, Client, Headers, Response, Timeout

    from toggl_api.meta.cache._base_cache import TogglCache, TogglQuery


log = logging.getLogger("toggl-api-wrapper.endpoint")


T = TypeVar("T", bound=TogglClass)


class TogglCachedEndpoint(TogglEndpoint[T]):
    """Abstract cached endpoint for requesting toggl API data to disk.

    See parent endpoint for more details.

    Params:
        auth: Authentication for the client.
        cache: Cache object for caching toggl API data to disk. Builtin cache
            types are JSONCache and SqliteCache.
        client: Optional client to be passed to be used for requests. Useful
            when a global client is used and needs to be recycled.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.

    Attributes:
        cache: Cache object the endpoint will use for storing models. Assigns
            itself as the parent automatically.

    Methods:
        request: Overriden method that implements the cache into the request chain.
        load_cache: Method for loading cache into memory.
        save_cache: Method for saving cache to disk. Ignored if expiry is set
            to 0 seconds.
        query: Wrapper method for accessing querying capabilities within the
            assigned cache.
    """

    __slots__ = ("_cache",)

    def __init__(
        self,
        auth: BasicAuth,
        cache: TogglCache[T] | None = None,
        *,
        client: Client | None = None,
        timeout: Timeout | int = 10,
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

    def request(  # type: ignore[override]
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
        data = self.load_cache() if self.cache and self.MODEL is not None else None
        if data and not refresh:
            log.info(
                "Loading request %s%s data from cache.",
                self.BASE_ENDPOINT,
                parameters,
                extra={"body": body, "headers": headers, "method": method},
            )
            return cast("list[T]", data)

        response = super().request(
            parameters,
            method=method,
            headers=headers,
            body=body,
            raw=raw,
        )
        if raw:
            return response

        if response is None or method == RequestMethod.DELETE:
            return None

        if self.cache and self.MODEL is not None:
            self.save_cache(response, method)  # type: ignore[arg-type]

        return response

    def load_cache(self) -> Iterable[T]:
        """Direct loading method for retrieving all models from cache.

        Raises:
            NoCacheAssignedError: If no cache is assigned to the endpoint.

        Returns:
            An iterable of models that have been previously saved.
        """
        if self.cache is None:
            raise NoCacheAssignedError

        return self.cache.load()

    def save_cache(
        self,
        response: list[T] | T,
        method: RequestMethod,
    ) -> None:
        """Direct saving method for retrieving all models from cache.

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
            return None
        return self.cache.save(response, method)

    def query(
        self,
        *query: TogglQuery[Any],
        distinct: bool = False,
    ) -> list[T]:
        """Query wrapper for the cache method.

        If the original data structure is required use the query on the
        *.cache* attribute instead.

        Args:
            *query: An arbitary amount of queries to match the models to.
            distinct: A boolean that remove duplicate values if present.

        Raises:
            NoCacheAssignedError: If the current cache is set to None.

        Returns:
            A list objects depending on the endpoint.
        """
        if self.cache is None:
            raise NoCacheAssignedError
        return list(self.cache.query(*query, distinct=distinct))

    @property
    def cache(self) -> TogglCache[T] | None:
        return self._cache

    @cache.setter
    def cache(self, value: TogglCache[T] | None) -> None:
        self._cache = value
        if self.cache and self.cache._parent is not self:  # noqa: SLF001
            self.cache.parent = self
