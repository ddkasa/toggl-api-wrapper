from __future__ import annotations

import contextlib
import json
import logging
import time
from collections import defaultdict
from collections.abc import Hashable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Final, Optional

from toggl_api.models import (
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

from .base_cache import Comparison, TogglCache, TogglQuery

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from toggl_api.meta import RequestMethod
    from toggl_api.meta.cached_endpoint import TogglCachedEndpoint

log = logging.getLogger("toggl-api-wrapper.cache")


@dataclass
class JSONSession:
    """Data structure for storing JSON in memory.

    Similar to a SQL session as its meant to have the same/similar interface.

    This dataclass doesn't require interaction from the library user and will
    be created in the json cache object.

    Examples:
        >>> cache = JSONSession(max_length=5000)

    Params:
        max_length: Max length of the data to be stored.

    Attributes:
        max_length: Max length of the data to be stored.
        version: Version of the data structure.
        data: List of Toggl objects stored in memory.
        modified: Timestamp of when the cache was last modified in nanoseconds.
            Used for checking if another cache object has updated it recently.

    Methods:
        save: Saves the data to a JSON file. Setting current timestamp and
            version.
        load: Loads the data from disk and stores it in the data attribute.
            Invalidates any entries older than expire argument.
        refresh: Utility method that checks if cache has been updated.
        process_data: Processes models according to set attributes.
    """

    max_length: int = field(default=10_000)
    version: str = field(init=False, default=version)
    data: list[TogglClass] = field(default_factory=list)
    modified: int = field(init=False, default=0)

    def refresh(self, path: Path) -> bool:
        if path.exists() and path.stat().st_mtime_ns > self.modified:
            self.modified = path.stat().st_mtime_ns
            self.data = self._diff(self._load(path)["data"], self.modified)
            return True
        return False

    def _save(self, path: Path, data: dict[str, Any]):
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, cls=CustomEncoder)

    def commit(self, path: Path) -> None:
        self.refresh(path)
        self.version = version
        data = {
            "version": self.version,
            "data": self.process_data(self.data),
        }
        self._save(path, data)

        self.modified = path.stat().st_mtime_ns

    def _diff(self, comp: list[TogglClass], mtime: int) -> list[TogglClass]:
        old_models = {m.id: m for m in self.data}
        new_models = {m.id: m for m in comp}

        model_ids: set[int] = set(old_models)
        model_ids.update(new_models)

        new_data: list[TogglClass] = []
        for mid in model_ids:
            old = old_models.get(mid)
            new = new_models.get(mid)
            if (old is None and new is not None) or (new and old and new.timestamp >= old.timestamp):
                new_data.append(new)
            elif old and old.timestamp.timestamp() * 10**9 >= mtime:
                new_data.append(old)

        return new_data

    def _load(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f, cls=CustomDecoder)

    def load(self, path: Path) -> None:
        if path.exists():
            data = self._load(path)
            self.modified = path.stat().st_mtime_ns
            self.version = data["version"]
            self.data = self.process_data(data["data"])
        else:
            self.version = version
            self.modified = time.time_ns()

    def process_data(self, data: list[TogglClass]) -> list[TogglClass]:
        data.sort(key=lambda x: x.timestamp or datetime.now(timezone.utc))
        return data[: self.max_length]


class JSONCache(TogglCache):
    """Class for caching Toggl data to disk in JSON format.

    Examples:
        >>> JSONCache(Path("cache"))

        >>> cache = JSONCache(Path("cache"), 3600)

        >>> cache = JSONCache(Path("cache"), timedelta(weeks=2))

    Params:
        path: Path to the cache file
        expire_after: Time after which the cache should be refreshed.
            If using an integer it will be assumed as seconds.
            If set to None the cache will never expire.
        parent: Parent endpoint that will use the cache. Assigned automatically
            when supplied to a cached endpoint.
        max_length: Max length list of the data to be stored permanently.

    Attributes:
        expire_after: Time after which the cache should be refreshed.

        session(JSONSession): Store the current json data in memory while
            handling the cache.

    Methods:
        commit: Wrapper for JSONSession.save() that saves the current json data
            to disk.
        save_cache: Saves the given data to the cache. Takes a list of Toggl
            objects or a single Toggl object as an argument and process the
            change before saving.
        load_cache: Loads the data from the cache and returns the data to the
            caller discarding expired entries.
    """

    __slots__ = ("session",)

    def __init__(
        self,
        path: Path,
        expire_after: Optional[timedelta | int] = None,
        parent: Optional[TogglCachedEndpoint] = None,
        *,
        max_length: int = 10_000,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.session = JSONSession(max_length=max_length)

    def commit(self) -> None:
        log.debug("Saving cache to disk!")
        self.session.commit(self.cache_path)

    def save_cache(
        self,
        update: Iterable[TogglClass] | TogglClass,
        method: RequestMethod,
    ) -> None:
        self.session.refresh(self.cache_path)
        func = self.find_method(method)
        if func is not None:
            func(update)
        self.commit()

    def load_cache(self) -> list[TogglClass]:
        self.session.load(self.cache_path)
        if self.expire_after is None:
            return self.session.data
        min_ts = datetime.now(timezone.utc) - self.expire_after
        return [m for m in self.session.data if m.timestamp >= min_ts]  # type: ignore[operator]

    def find_entry(
        self,
        entry: TogglClass | dict[str, int],
        **kwargs,
    ) -> TogglClass | None:
        self.session.refresh(self.cache_path)
        if not self.session.data or self.parent is None:
            return None
        for item in self.session.data:
            if item is not None and item["id"] == entry["id"] and isinstance(item, self.parent.model):
                return item
        return None

    def add_entry(self, item: TogglClass) -> None:
        find_entry = self.find_entry(item)
        if find_entry is None:
            return self.session.data.append(item)
        index = self.session.data.index(find_entry)
        item.timestamp = datetime.now(timezone.utc)
        self.session.data[index] = item
        return None

    def add_entries(self, update: list[TogglClass] | TogglClass, **kwargs) -> None:
        if isinstance(update, TogglClass):
            return self.add_entry(update)
        for item in update:
            self.add_entry(item)
        return None

    def update_entries(self, update: list[TogglClass] | TogglClass, **kwargs) -> None:
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

    def query(self, *query: TogglQuery, distinct: bool = False) -> list[TogglClass]:
        """Query method for filtering Toggl objects from cache.

        Filters cached Toggl objects by set of supplied queries.

        Supports queries with various comparisons with the [Comparison][toggl_api.Comparison]
        enumeration.

        Args:
            query: Any positional argument that is used becomes query argument.
            distinct: Whether to keep the same values around. This doesn't work
                with unhashable fields such as lists.

        Raises:
            ValueError: If parent has not been set.

        Returns:
            list[TogglClass]: A query object with parameters filtered.
        """
        if self.parent is None:
            msg = "Cannot load cache without parent!"
            raise ValueError(msg)

        log.debug("Querying cache with %s parameters.", len(query), extra={"query": query})

        min_ts = datetime.now(timezone.utc) - self.expire_after if self.expire_after else None
        self.session.load(self.cache_path)
        search = self.session.data
        existing: defaultdict[str, set[Any]] = defaultdict(set)

        return [
            model
            for model in search
            if self._query_helper(
                model,
                query,
                existing,
                min_ts,
                distinct=distinct,
            )
        ]

    def _query_helper(
        self,
        model: TogglClass,
        queries: tuple[TogglQuery, ...],
        existing: dict[str, set[Any]],
        min_ts: Optional[datetime],
        *,
        distinct: bool,
    ) -> bool:
        if self.expire_after and min_ts and model.timestamp and min_ts >= model.timestamp:
            return False

        for query in queries:
            if (
                distinct and not isinstance(query.value, list) and model[query.key] in existing[query.key]
            ) or not self._match_query(model, query):
                return False

        if distinct:
            for query in queries:
                value = model[query.key]
                if isinstance(value, Hashable):
                    existing[query.key].add(value)

        return True

    @staticmethod
    def _match_equal(model: TogglClass, query: TogglQuery):
        if isinstance(query.value, Sequence) and not isinstance(query.value, str):
            value = model[query.key]

            if isinstance(value, Sequence) and not isinstance(value, str):
                return any(v == comp for comp in query.value for v in value)

            return any(value == comp for comp in query.value)

        return model[query.key] == query.value

    @staticmethod
    def _match_query(model: TogglClass, query: TogglQuery) -> bool:
        if query.comparison == Comparison.EQUAL:
            return JSONCache._match_equal(model, query)
        if query.comparison == Comparison.LESS_THEN:
            return model[query.key] < query.value
        if query.comparison == Comparison.LESS_THEN_OR_EQUAL:
            return model[query.key] <= query.value
        if query.comparison == Comparison.GREATER_THEN:
            return model[query.key] > query.value
        if query.comparison == Comparison.GREATER_THEN_OR_EQUAL:
            return model[query.key] >= query.value
        msg = f"{query.comparison} is not implemented!"
        raise NotImplementedError(msg)

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
            self.session.load(self.cache_path)


class CustomEncoder(json.encoder.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return timedelta.total_seconds(obj)
        if isinstance(obj, TogglClass):
            return as_dict_custom(obj)
        return super().default(obj)


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
