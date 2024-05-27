from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Final, Optional

from toggl_api.modules.meta.enums import RequestMethod

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import timedelta
    from pathlib import Path

    from toggl_api.modules.meta import TogglCachedEndpoint
    from toggl_api.modules.models import TogglClass


class TogglCache(metaclass=ABCMeta):
    """Abstract class for caching toggl API data to disk.

    Integrates fully with TogglCachedEndpoint to create a seemless depending on
    the users choice of cache.


    Abstract Methods:
        load_cache:
        save_cache
        find_entry
        add_entry
        update_entry
        delete_entry

    Methods:
        find_method: Matches a RequestMethod to cache functionality.
        parent_exist: Validates if the parent has been set. The parent will be
            generally set by the endpoint when assigned.

    Attributes:
        _cache_path: Path to the cache file. Will generate the folder if it
            does not exist.
        _expire_after: Time after which the cache should be refreshed
        _parent: Parent TogglCachedEndpoint
    """

    __slots__ = ("_cache_path", "_expire_after", "_parent")

    def __init__(
        self,
        path: Path,
        expire_after: timedelta,
        parent: Optional[TogglCachedEndpoint] = None,
    ) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self._cache_path = path
        self._expire_after = expire_after
        self._parent = parent

    @abstractmethod
    def load_cache(self) -> list[TogglClass]:
        pass

    @abstractmethod
    def save_cache(self, data: list[TogglClass], method: RequestMethod) -> None:
        pass

    @abstractmethod
    def find_entry(self, **kwargs) -> list[TogglClass]:
        pass

    @abstractmethod
    def add_entries(
        self,
        data: list[TogglClass],
        update: list[TogglClass],
        **kwargs,
    ) -> None:
        pass

    @abstractmethod
    def update_entries(
        self,
        data: list[TogglClass],
        update: list[TogglClass],
        **kwargs,
    ) -> TogglClass | None:
        pass

    @abstractmethod
    def delete_entries(
        self,
        data: list[TogglClass],
        update: list[TogglClass],
        **kwargs,
    ) -> TogglClass | None:
        pass

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        return self._cache_path

    @property
    def expire_after(self) -> timedelta:
        return self._expire_after

    @expire_after.setter
    def expire_after(self, value: timedelta) -> None:
        self._expire_after = value

    @property
    def parent(self) -> TogglCachedEndpoint | None:
        return self._parent

    @parent.setter
    def parent(self, value: Optional[TogglCachedEndpoint]) -> None:
        self._parent = value

    def find_method(self, method: RequestMethod) -> Callable | None:
        match_func: Final[dict[RequestMethod, Callable]] = {
            RequestMethod.GET: self.add_entries,
            RequestMethod.POST: self.update_entries,
            RequestMethod.PATCH: self.update_entries,
            RequestMethod.PUT: self.add_entries,
            # RequestMethod.DELETE: self.delete_entries,
        }
        return match_func.get(method)

    def parent_exists(self) -> None:
        if self.parent is not None:
            return
        msg = "Parent is not setup!"
        raise TypeError(msg)
