from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Final, Optional

from toggl_api.modules.models import (
    TogglClass,
    TogglClient,
    TogglProject,
    TogglTag,
    TogglTracker,
    TogglWorkspace,
    as_dict_custom,
)
from toggl_api.utility import parse_iso
from toggl_api.version import version

from .base_cache import TogglCache

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from toggl_api.modules.meta import RequestMethod
    from toggl_api.modules.meta.cached_endpoint import TogglCachedEndpoint


@dataclass
class JSONSession:
    """Data structure for storing JSON in memory.

    Similar to a SQL session as its meant to have the same/similar interface.

    Methods:
        save: Saves the data to a JSON file. Setting current timestamp and
            version.
        load: Loads the data from disk and stores it in the data attribute.
            Invalidates any entries older than expire argument.

    Attributes:
        max_length: Max length of the data to be stored.
        timestamp: Timestamp of the data for when it was loaded.
        version: Version of the data structure.
        data: List of Toggl objects stored in memory.
    """

    # TODO: Implement max length of data.
    max_length: int = field(default=10_000)
    timestamp: datetime = field(init=False)
    version: str = field(init=False, default=version)
    data: list[TogglClass] = field(default_factory=list)

    def commit(self, path: Path) -> None:
        self.timestamp = datetime.now(timezone.utc)
        self.version = version
        data = {
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "data": self.process_data(self.data),
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, cls=CustomEncoder)

    def load(self, path: Path, expire_after: timedelta) -> None:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f, cls=CustomDecoder)
            self.timestamp = parse_iso(data["timestamp"])  # type: ignore[assignment]
            self.version = data["version"]
            self.data = self.process_data(data["data"])

        else:
            self.timestamp = datetime.now(timezone.utc)
            self.version = version

    def process_data(self, data: list[TogglClass]) -> list[TogglClass]:
        data.sort(key=lambda x: x.timestamp or datetime.now(timezone.utc))
        return data[: self.max_length]


class JSONCache(TogglCache):
    """Class for caching Toggl data to disk in JSON format.

    Args:
        path: Path to the cache file
        expire_after: Time after which the cache should be refreshed
        parent: Parent endpoint that will use the cache. Usually assigned
            automatically when supplied to a cached endpoint.
        max_length: Max length of the data to be stored.

    Methods:
        commit: Wrapper for JSONSession.save() that saves the current json data
            to disk.
        save_cache: Saves the given data to the cache. Takes a list of Toggl
            objects or a single Toggl object as an argument and process the
            change before saving.
        load_cache: Loads the data from the cache and returns the data to the
            caller discarding expired entries.

    Attributes:
        session(JSONSession): Store the current json data in memory while
            handling the cache.
    """

    __slots__ = ("session",)

    # TODO: Consider creating a 'session' object to manage the cache persistently.

    def __init__(
        self,
        path: Path,
        expire_after: timedelta,
        parent: Optional[TogglCachedEndpoint] = None,
        *,
        max_length: int = 10_000,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.session = JSONSession(max_length=max_length)

    def commit(self) -> None:
        self.session.commit(self.cache_path)

    def save_cache(
        self,
        update: Iterable[TogglClass] | TogglClass,
        method: RequestMethod,
    ) -> None:
        func = self.find_method(method)
        if func is not None:
            func(update)
        self.commit()

    def load_cache(self, *, expire: bool = True) -> list[TogglClass]:
        self.session.load(self.cache_path, self.expire_after)
        min_ts = datetime.now(timezone.utc) - self.expire_after
        return [m for m in self.session.data if not expire or m.timestamp >= min_ts]  # type: ignore[operator]

    def find_entry(
        self,
        entry: TogglClass | dict,
        **kwargs,
    ) -> Optional[TogglClass]:
        if not self.session.data:
            return None
        for item in self.session.data:
            if entry is not None and item["id"] == entry["id"] and type(entry) == type(item):
                return item
        return None

    def add_entry(
        self,
        item: TogglClass,
    ) -> None:
        find_entry = self.find_entry(item)
        if find_entry is None:
            return self.session.data.append(item)
        index = self.session.data.index(find_entry)
        item.timestamp = datetime.now(timezone.utc)
        self.session.data[index] = item
        return None

    def add_entries(
        self,
        update: list[TogglClass] | TogglClass,
        **kwargs,
    ) -> None:
        if isinstance(update, TogglClass):
            return self.add_entry(update)
        for item in update:
            self.add_entry(item)
        return None

    def update_entries(
        self,
        update: list[TogglClass] | TogglClass,
        **kwargs,
    ) -> None:
        self.add_entries(update)

    def delete_entry(self, entry: TogglClass) -> None:
        find_entry = self.find_entry(entry)
        if not find_entry:
            return
        index = self.session.data.index(find_entry)
        self.session.data.pop(index)

    def delete_entries(
        self,
        update: list[TogglClass] | TogglClass,
        **kwargs,
    ) -> None:
        if isinstance(update, TogglClass):
            return self.delete_entry(update)
        for entry in update:
            self.delete_entry(entry)
        return None

    def query(
        self,
        *,
        inverse: bool = False,
        distinct: bool = False,
        expire: bool = True,
        **query: dict[str, Any],
    ) -> list[TogglClass]:
        # TODO: Implementation details are still lacking here.
        if self.parent is None:
            msg = "Cannot load cache without parent!"
            raise ValueError(msg)

        self.session.load(self.cache_path, self.expire_after)
        search = self.session.data
        min_ts = datetime.now(timezone.utc) - self.expire_after
        results: list[TogglClass] = []
        existing_values: set[Any] = set()

        for model in search:
            if expire and model.timestamp and min_ts >= model.timestamp:
                continue
            if all(model[key] == value for key, value in query.items()) and (
                not distinct or all(model[k] not in existing_values for k in query)
            ):
                if distinct:
                    existing_values.add(query.values())
                results.append(model)
        if inverse:
            results.reverse()
        return results

    @property
    def cache_path(self) -> Path:
        if self.parent is None:
            return self._cache_path / "cache.json"
        return self._cache_path / f"cache_{self.parent.model.__tablename__}.json"

    @property
    def parent(self) -> TogglCachedEndpoint | None:
        return super().parent

    @parent.setter
    def parent(self, parent: Optional[TogglCachedEndpoint]) -> None:
        self._parent = parent
        if parent is not None:
            self.session.load(self.cache_path, self.expire_after)


class CustomEncoder(json.encoder.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, timedelta):
            return timedelta.total_seconds(o)
        if isinstance(o, TogglClass):
            return as_dict_custom(o)
        return super().default(o)


class CustomDecoder(json.decoder.JSONDecoder):
    MATCH_DICT: Final[dict[str, type[TogglClass]]] = {
        TogglClient.__tablename__: TogglClient,
        TogglProject.__tablename__: TogglProject,
        TogglTag.__tablename__: TogglTag,
        TogglTracker.__tablename__: TogglTracker,
        TogglWorkspace.__tablename__: TogglWorkspace,
    }

    def decode(self, obj: Any) -> Any:  # type: ignore[override]
        if obj and isinstance(obj, str):
            with contextlib.suppress(json.decoder.JSONDecodeError):
                obj = super().decode(obj)

        if isinstance(obj, dict):
            if "timestamp" in obj and isinstance(obj["timestamp"], str):
                obj["timestamp"] = parse_iso(obj["timestamp"])
            for k, v in obj.items():
                obj[k] = self.decode(v)
            if "class" in obj:
                cls: str = obj.pop("class")
                obj = self.MATCH_DICT[cls].from_kwargs(**obj)

        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                obj[i] = self.decode(v)

        return obj
