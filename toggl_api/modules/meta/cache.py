from __future__ import annotations

import json
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

import sqlalchemy as db

from toggl_api.modules.models import register_tables
from toggl_api.utility import parse_iso
from toggl_api.version import version

from .meta import RequestMethod, TogglEndpoint

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    import httpx

    from toggl_api.modules.models import TogglClass


class TogglCache(metaclass=ABCMeta):
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
    def load_cache(self) -> list:
        pass

    @abstractmethod
    def save_cache(self, data: Iterable[dict[str, Any]]) -> None:
        return None

    @abstractmethod
    def find_model(
        self,
        data: Iterable[dict[str, Any]],
        query: str | int,
    ) -> TogglClass | None:
        return None

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


class JSONCache(TogglCache):
    def find_model(
        self,
        data: Iterable[dict[str, Any]],
        query: str | int,
    ) -> TogglClass | None:
        if self.parent is None:
            return None
        for item in data:
            if query in (item["id"], item["name"]):
                return self.parent.model.from_kwargs(**item)

        return None

    def save_cache(self, data: Iterable) -> None:
        data = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "data": data,
            "version": version,
        }
        with self.cache_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_cache(self) -> list:
        now = datetime.now(tz=timezone.utc)
        if not self.cache_path.exists():
            return []
        with self.cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if now - self.expire_after <= parse_iso(data["timestamp"]):
            return data["data"]

        return []

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

    def save_cache(self, data: Iterable) -> None:
        return

    def load_cache(self) -> list:
        return []

    def add_entry(self, **kwargs) -> None:
        return None

    def update_entry(self, row_id: int, **kwargs) -> None:
        return None

    def delete_entry(self, row_id: int) -> None:
        return None

    def find_model() -> TogglClass | None:
        return

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
            data = self.load_cache()
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

        self.save_cache(response)

        return response

    def load_cache(self) -> None | list:
        if not self.cache.cache_path.exists():
            return []
        return self.cache.load_cache()

    def save_cache(self, data: Iterable) -> None:
        if not self.cache.expire_after.total_seconds():
            return None
        return self.cache.save_cache(data)

    def process_models(self, data: list[dict]) -> list:
        return [self.model.from_kwargs(**tracker) for tracker in data]

    @property
    @abstractmethod
    def endpoint(self) -> str:
        return super().endpoint
