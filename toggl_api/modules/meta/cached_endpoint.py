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
from typing import TYPE_CHECKING, Any, Optional

from .base_endpoint import TogglEndpoint
from .enums import RequestMethod

if TYPE_CHECKING:
    from collections.abc import Iterable

    import httpx

    from toggl_api.modules.models import TogglClass

    from .cache import TogglCache

log = logging.getLogger("toggl-api")


# REFACTOR: Possibly turn this into a mixin to avoid duplication and more flexibility.
class TogglCachedEndpoint(TogglEndpoint):
    """Abstract cached endpoint for requesting toggl API data to disk.

    Attributes:
        _cache: Cache object for caching toggl API data to disk. Builtin cache
            types are JSONCache and SqliteCache.
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
    ) -> Optional[TogglClass | Iterable[TogglClass]]:
        """Overridden request method with builtin cache.

        Args:
            parameters: Request parameters with the endpoint excluded.
            headers: Request headers. Custom headers can be added here.
            body: Request body for GET, POST, PUT, PATCH requests.
                Defaults to None.
            method: Request method. Defaults to GET.
            refresh: Whether to refresh the cache or not. Defaults to False.

        Returns:
            TogglClass | Iterable[TogglClass] | None: Toggl API response data
                processed into TogglClass objects.
        """

        data = self.load_cache()
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
        )

        if response is None or method == RequestMethod.DELETE:
            return None

        self.save_cache(response, method)  # type: ignore[arg-type]

        return response

    def load_cache(self) -> Iterable[TogglClass]:
        return self.cache.load_cache()

    def save_cache(
        self,
        response: list[TogglClass] | TogglClass,
        method: RequestMethod,
    ) -> None:
        if not self.cache.expire_after.total_seconds():
            return None
        return self.cache.save_cache(response, method)

    def query(
        self,
        *,
        inverse: bool = False,
        distinct: bool = False,
        expire: bool = True,
        **query: dict[str, Any],
    ) -> Iterable[TogglClass]:
        return self.cache.query(
            inverse=inverse,
            distinct=distinct,
            expire=expire,
            **query,
        )

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
        if self.cache.parent is None:
            self.cache.parent = self
