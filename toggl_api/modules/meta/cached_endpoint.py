"""Module that deals with caching API data permanently to disk.

Classes:
    TogglCache: Abstract class for caching toggl API data to disk.
    JSONCache: Class for caching data to disk in JSON format.
    SqliteCache: Class for caching data to disk in sqlite format.
    TogglCachedEndpoint: Abstract class for caching and requesting toggl API
        data to disk.

"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from .base_endpoint import TogglEndpoint
from .enums import RequestMethod

if TYPE_CHECKING:
    import httpx

    from toggl_api.modules.models import TogglClass

    from .cache import TogglCache


# REFACTOR: Possibly turn this into a mixin to avoid duplication and more flexibility.
class TogglCachedEndpoint(TogglEndpoint):
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
    ) -> dict | list | None:
        data = self.load_cache()
        if data and refresh:
            return data

        response = super().request(
            parameters,
            method=method,
            headers=headers,
            body=body,
        )

        if not isinstance(response, Sequence):
            response = [response]

        self.save_cache(data, response, method)

        return response

    def load_cache(self) -> list:
        return self.cache.load_cache()

    def save_cache(
        self,
        data: Sequence[TogglClass],
        response: list[TogglClass],
        method: RequestMethod,
    ) -> None:
        if not self.cache.expire_after.total_seconds():
            return None
        return self.cache.save_cache(data, response, method)

    def process_models(self, data: Sequence[dict[str, Any]]) -> list[TogglClass]:
        return [self.model.from_kwargs(**tracker) for tracker in data]

    @property
    @abstractmethod
    def endpoint(self) -> str:
        return super().endpoint

    @property
    def cache(self) -> TogglCache:
        return self._cache

    @cache.setter
    def cache(self, value: TogglCache) -> None:
        self._cache = value
        if self.cache.parent is None:
            self.cache.parent = self
