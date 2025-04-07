"""SQLite cache module."""
# ruff: noqa: E402

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Sequence
from datetime import timedelta
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Generic, TypeVar, cast

from toggl_api._exceptions import MissingParentError
from toggl_api.meta._enums import RequestMethod
from toggl_api.models import TogglClass

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from os import PathLike

    from ._async_endpoint import TogglAsyncCachedEndpoint


T = TypeVar("T", bound=TogglClass)


class TogglAsyncCache(ABC, Generic[T]):
    """Abstract class for caching Toggl API data to disk.

    Integrates as the backend for the [TogglCachedEndpoint][toggl_api.meta.TogglCachedEndpoint]
    in order to store requested models locally.

    Params:
        path: Location where the cache will be saved.
        expire_after: After how much time should the cache expire.
            Set to None if no expire_date or to **0** seconds for no caching
            at all. If using an integer it will be assumed as seconds.
            If set to None its ignored.
        parent: Endpoint which the cache belongs to. Doesn't need to be set
            through parameters as it will be auto assigned.

    Attributes:
        cache_path: Path to the cache file. Will generate the folder if it
            does not exist.
        expire_after: Time after which the cache should be refreshed.
        parent: Parent TogglCachedEndpoint

    Methods:
        commit: Commits the cache to disk, database or other form.
            Method for finalising the cache. Abstract.
        load_cache: Loads the cache from disk, database or other form. Abstract.
        save_cache: Saves and preforms action depending on request type. Abstract.
        find_entry: Looks for a TogglClass in the cache. Abstract.
        add_entry: Adds a TogglClass to the cache. Abstract.
        update_entry: Updates a TogglClass in the cache. Abstract.
        delete_entry: Deletes a TogglClass from the cache. Abstract.
        find_method: Matches a RequestMethod to cache functionality.
        parent_exist: Validates if the parent has been set. The parent will be
            generally set by the endpoint when assigned. Abstract.

    Raises:
        MissingParentError: If the parent is None and any cache method is being
            accessed.
    """

    __slots__ = ("_cache_path", "_expire_after", "_parent")

    def __init__(
        self,
        path: Path | PathLike[str],
        expire_after: timedelta | int | None = None,
        parent: TogglAsyncCachedEndpoint[T] | None = None,
    ) -> None:
        self._cache_path = path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        self._expire_after = timedelta(seconds=expire_after) if isinstance(expire_after, int) else expire_after
        self._parent = parent

    @abstractmethod
    async def load(self) -> Iterable[T]: ...

    async def save(self, entry: list[T] | T, method: RequestMethod) -> None:
        func = self.find_method(method)
        if func is None:
            return
        await (func(*entry) if isinstance(entry, Sequence) else func(entry))

    @abstractmethod
    async def find(self, pk: int) -> T | None: ...

    @abstractmethod
    async def add(self, *entries: T) -> None: ...

    @abstractmethod
    async def update(self, *entries: T) -> None: ...

    @abstractmethod
    async def delete(self, *entries: T) -> None: ...

    def find_method(
        self,
        method: RequestMethod,
    ) -> Callable[[Any], Awaitable[Any]] | None:
        match_func: Final[dict[RequestMethod, Callable[[Any], Awaitable[Any]]]] = {
            RequestMethod.GET: self.add,
            RequestMethod.POST: self.add,
            RequestMethod.PATCH: self.update,
            RequestMethod.PUT: self.add,
        }
        return match_func.get(method)

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        return self._cache_path

    @property
    def expire_after(self) -> timedelta | None:
        return self._expire_after

    @expire_after.setter
    def expire_after(self, value: timedelta | None = None) -> None:
        self._expire_after = value

    @property
    def parent(self) -> TogglAsyncCachedEndpoint[T]:
        if self._parent is None:
            msg = "Can not use cache without a parent set!"
            raise MissingParentError(msg)

        return self._parent

    @parent.setter
    def parent(self, value: TogglAsyncCachedEndpoint[T] | None) -> None:
        self._parent = value

    @property
    def model(self) -> type[T]:
        return cast("type[T]", self.parent.MODEL)
