from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Final, Generic, Optional, TypeVar

from toggl_api.meta.enums import RequestMethod

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from pathlib import Path

    from toggl_api.meta import TogglCachedEndpoint
    from toggl_api.models import TogglClass


class Comparison(enum.Enum):
    EQUAL = enum.auto()
    LESS_THEN = enum.auto()
    LESS_THEN_OR_EQUAL = enum.auto()
    GREATER_THEN = enum.auto()
    GREATER_THEN_OR_EQUAL = enum.auto()


T = TypeVar("T")


@dataclass
class TogglQuery(Generic[T]):
    """Dataclass for querying cached Toggl models."""

    key: str = field()
    """Name of the target column to compare against."""
    value: T | Sequence[T] = field()
    """Value to compare against."""
    comparison: Comparison = field(default=Comparison.EQUAL)
    """The way the value should be compared. None 'EQUALS' comparisons for None numeric or time based values."""

    def __post_init__(self) -> None:
        if not isinstance(self.value, date | int | timedelta) and self.comparison != Comparison.EQUAL:
            msg = "None 'EQUAL' comparisons only available for time or numeric based values."
            raise TypeError(msg)

        if isinstance(self.value, date) and not isinstance(self.value, datetime):
            if self.comparison in {
                Comparison.LESS_THEN,
                Comparison.GREATER_THEN_OR_EQUAL,
            }:
                self.value = datetime.combine(  # type: ignore[assignment]
                    self.value,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )
            else:
                self.value = datetime.combine(  # type: ignore[assignment]
                    self.value,
                    datetime.max.time(),
                    tzinfo=timezone.utc,
                )


class TogglCache(ABC):
    """Abstract class for caching toggl API data to disk.

    Integrates fully with TogglCachedEndpoint to create a seemless depending on
    the users choice of cache.

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
        query: Queries the cache for various varibles. Abstract.

    Attributes:
        cache_path: Path to the cache file. Will generate the folder if it
            does not exist.
        expire_after: Time after which the cache should be refreshed.
            If using an integer it will be assumed as seconds.
            If set to None its ignored.
        parent: Parent TogglCachedEndpoint
    """

    __slots__ = ("_cache_path", "_expire_after", "_parent")

    def __init__(
        self,
        path: Path,
        expire_after: Optional[timedelta | int] = None,
        parent: Optional[TogglCachedEndpoint] = None,
    ) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self._cache_path = path

        self._expire_after = timedelta(seconds=expire_after) if isinstance(expire_after, int) else expire_after
        self._parent = parent

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def load_cache(self) -> Iterable[TogglClass]: ...

    @abstractmethod
    def save_cache(self, entry: list[TogglClass] | TogglClass, method: RequestMethod) -> None: ...

    @abstractmethod
    def find_entry(self, entry: TogglClass | dict[str, Any]) -> TogglClass | None: ...

    @abstractmethod
    def add_entries(self, update: list[TogglClass]) -> None: ...

    @abstractmethod
    def update_entries(self, update: list[TogglClass] | TogglClass) -> None: ...

    @abstractmethod
    def delete_entries(self, update: list[TogglClass] | TogglClass) -> None: ...

    @abstractmethod
    def query(self, *query: TogglQuery, distinct: bool = False) -> Iterable[TogglClass]: ...

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        return self._cache_path

    @property
    def expire_after(self) -> timedelta | None:
        return self._expire_after

    @expire_after.setter
    def expire_after(self, value: Optional[timedelta] = None) -> None:
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
        }
        return match_func.get(method)
