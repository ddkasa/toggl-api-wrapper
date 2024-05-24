from __future__ import annotations

import json
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Final, Optional

import sqlalchemy as db
from sqlalchemy.orm import Session

from toggl_api.modules.models import register_tables
from toggl_api.utility import parse_iso
from toggl_api.version import version

from .meta import RequestMethod, TogglEndpoint

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

    import httpx

    from toggl_api.modules.models import TogglClass


class TogglCache(metaclass=ABCMeta):
    """Abstract class for caching toggl API data to disk.

    Attributes:
        _cache_path: Path to the cache file
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
    def load_cache(self, method: RequestMethod) -> list[TogglClass]:
        pass

    @abstractmethod
    def save_cache(self, data: list[TogglClass], method: RequestMethod) -> None:
        pass

    @abstractmethod
    def find_entry(self, **kwargs) -> list[TogglClass]:
        pass

    @abstractmethod
    def add_entry(self, entry: TogglClass) -> None:
        pass

    @abstractmethod
    def update_entry(self, entry: TogglClass) -> TogglClass | None:
        pass

    @abstractmethod
    def delete_entry(self, entry: TogglClass) -> TogglClass | None:
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
            RequestMethod.GET: self.find_entry,
            RequestMethod.POST: self.update_entry,
            RequestMethod.PATCH: self.update_entry,
            RequestMethod.PUT: self.add_entry,
            RequestMethod.DELETE: self.delete_entry,
        }
        return match_func.get(method)

    def parent_exists(self) -> None:
        if isinstance(self.parent, TogglCachedEndpoint):
            return
        msg = "Parent is not setup!"
        raise TypeError(msg)


class JSONCache(TogglCache):
    """Class for caching data to disk in JSON format.

    Args:
        path: Path to the cache file
        expire_after: Time after which the cache should be refreshed
        parent: Parent TogglCachedEndpoint

    """

    def save_cache(self, data: Iterable, method: RequestMethod) -> None:
        self.parent_exists()
        data = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "data": data,
            "version": version,
        }
        with self.cache_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_cache(self) -> list[TogglClass]:
        self.parent_exists()
        now = datetime.now(tz=timezone.utc)
        if not self.cache_path.exists():
            return []
        with self.cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if now - self.expire_after <= parse_iso(data["timestamp"]):
            return self.parent.process_models(data["data"])  # type: ignore[union-attr]

        return []

    def find_entry(self, **kwargs) -> list[TogglClass]:
        data = self.load_cache()

        entries: list[TogglClass] = []
        for item in data:
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                entries.append(item)  # noqa: PERF401

        return entries

    def add_entry(self, entry: TogglClass) -> None:
        pass

    def update_entry(self, entry: TogglClass) -> TogglClass | None:
        pass

    def delete_entry(self, entry: TogglClass) -> TogglClass | None:
        pass

    @property
    def cache_path(self) -> Path:
        return self._cache_path / "cache.json"


class SqliteCache(TogglCache):
    __slots__ = ("database", "metadata")

    def __init__(
        self,
        path: Path,
        expire_after: timedelta,
        parent: Optional[TogglCachedEndpoint] = None,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.database = db.create_engine(f"sqlite:///{self.cache_path}")
        with self.database.connect():
            self.metadata = register_tables(self.database)

    def save_cache(self, data: TogglClass, method: RequestMethod) -> None:
        func = self.find_method(method)
        if func is None:
            return None

        return func(data)

    def load_cache(self, method: RequestMethod) -> list[TogglClass]:
        return []

    def add_entry(self, entry: TogglClass) -> None:
        if self.parent is None:
            return
        with Session(self.database) as session:
            session.add(entry)
            session.commit()

    def update_entry(self, entry: TogglClass) -> None:
        with Session(self.database) as session:
            session.add(entry)
            session.commit()

    def delete_entry(self, entry: TogglClass) -> None:
        with Session(self.database) as session:
            session.delete(entry)
            session.commit()

    def find_entry(  # type: ignore[override]
        self,
        query: TogglClass,
    ) -> TogglClass | None:
        if self.parent is None:
            return None
        with Session(self.database) as session:
            return session.query(self.parent.model).get(query)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "cache.sqlite"


class TogglCachedEndpoint(TogglEndpoint):
    __slots__ = ("cache",)

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
        if self.cache.parent is None:
            self.cache.parent = self

    def request(  # type: ignore[override]
        self,
        parameters: str,
        headers: Optional[dict] = None,
        method: RequestMethod = RequestMethod.GET,
        *,
        refresh: bool = False,
    ) -> dict | list | None:
        if not refresh and method == RequestMethod.GET:
            data = self.load_cache(method)
            if data:
                return data
        else:
            data = []

        response = super().request(
            parameters,
            method=method,
            headers=headers,
        )
        if response is None:
            return None

        if not isinstance(response, Sequence):
            response = [response]

        self.save_cache(response, method)

        return response

    def load_cache(self, method: RequestMethod) -> list:
        return self.cache.load_cache(method)

    def save_cache(self, data: Sequence[TogglClass], method: RequestMethod) -> None:
        if not self.cache.expire_after.total_seconds():
            return None
        return self.cache.save_cache(data, method)

    def process_models(self, data: Sequence[dict[str, Any]]) -> list[TogglClass]:
        return [self.model.from_kwargs(**tracker) for tracker in data]

    @property
    @abstractmethod
    def endpoint(self) -> str:
        return super().endpoint
