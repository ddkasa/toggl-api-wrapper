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
from abc import abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Optional

from .base_endpoint import TogglEndpoint
from .enums import RequestMethod

if TYPE_CHECKING:
    from collections.abc import Iterable

    import httpx

    from toggl_api.meta.cache.base_cache import TogglQuery
    from toggl_api.modules.models import TogglClass

    from .cache import TogglCache

log = logging.getLogger("toggl-api-wrapper.endpoint")


class TogglCachedEndpoint(TogglEndpoint):
    """Abstract cached endpoint for requesting toggl API data to disk.

    See parent endpoint for more details.

    Params:
        cache: Cache object for caching toggl API data to disk. Builtin cache
            types are JSONCache and SqliteCache.

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
        workspace_id: int,
        auth: httpx.BasicAuth,
        cache: TogglCache,
        *,
        timeout: int = 20,
        **kwargs,
    ) -> None:
        super().__init__(
            workspace_id=workspace_id,
            auth=auth,
            timeout=timeout,
            **kwargs,
        )
        self.cache = cache

    def request(  # type: ignore[override]  # noqa: PLR0913
        self,
        parameters: str,
        headers: Optional[dict] = None,
        body: Optional[dict] = None,
        method: RequestMethod = RequestMethod.GET,
        *,
        refresh: bool = False,
        raw: bool = False,
    ) -> Any:
        """Overridden request method with builtin cache.

        Args:
            parameters: Request parameters with the endpoint excluded.
            headers: Request headers. Custom headers can be added here.
            body: Request body for GET, POST, PUT, PATCH requests.
                Defaults to None.
            method: Request method. Defaults to GET.
            refresh: Whether to refresh the cache or not. Defaults to False.
            raw (bool): Whether to use the raw data. Defaults to False.

        Returns:
            TogglClass | Iterable[TogglClass] | None: Toggl API response data
                processed into TogglClass objects.
        """

        data = self.load_cache() if self.model is not None else None
        if data and not refresh:
            log.info(
                "Loading request %s%s data from cache.",
                self.endpoint,
                parameters,
                extra={"body": body, "headers": headers, "method": method},
            )
            return data

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

        if self.model is not None:
            self.save_cache(response, method)  # type: ignore[arg-type]

        return response

    def load_cache(self) -> Iterable[TogglClass]:
        """Direct loading method for retrieving all models from cache."""
        return self.cache.load_cache()

    def save_cache(
        self,
        response: list[TogglClass] | TogglClass,
        method: RequestMethod,
    ) -> None:
        """Direct saving method for retrieving all models from cache."""
        if isinstance(self.cache.expire_after, timedelta) and not self.cache.expire_after.total_seconds():
            return None
        return self.cache.save_cache(response, method)

    def query(self, *query: TogglQuery, distinct: bool = False) -> Iterable[TogglClass]:
        """Query wrapper for the cache method.

        Args:
            query: An arbitary amount of queries to match the models to.
            distinct: A boolean that remove duplicate values if present.

        Returns:
            iterable: An iterable object depending on the cache used.
        """
        return self.cache.query(*query, distinct=distinct)

    @property
    @abstractmethod
    def endpoint(self) -> str:
        pass

    @property
    def cache(self) -> TogglCache:
        return self._cache

    @cache.setter
    def cache(self, value: TogglCache) -> None:
        self._cache = value
        if self.cache.parent is not self:
            self.cache.parent = self
