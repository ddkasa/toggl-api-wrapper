from __future__ import annotations

import contextlib
import json
from dataclasses import asdict, dataclass, field
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
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from toggl_api.modules.meta import RequestMethod
    from toggl_api.modules.meta.cached_endpoint import TogglCachedEndpoint


@dataclass
class JSONSession:
    timestamp: datetime = field(init=False)
    version: str = field(init=False, default=version)
    data: list[TogglClass] = field(default_factory=list)

    def save(self, path: Path) -> None:
        self.timestamp = datetime.now(timezone.utc)
        self.version = version
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, cls=CustomEncoder)

    def load(self, path: Path, expire: timedelta) -> None:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f, cls=CustomDecoder)
            self.timestamp = parse_iso(data["timestamp"])
            self.version = data["version"]
            min_ts = datetime.now(timezone.utc) - expire
            self.data = [m for m in data["data"] if m.timestamp >= min_ts]
        else:
            self.timestamp = datetime.now(timezone.utc)
            self.version = version


class JSONCache(TogglCache):
    """Class for caching Toggl data to disk in JSON format.

    Args:
        path: Path to the cache file
        expire_after: Time after which the cache should be refreshed
        parent: Parent TogglCachedEndpoint
        session: Store the current json data in memory while handling the cache.

    """

    __slots__ = ("session",)

    # TODO: Consider creating a 'session' object to manage the cache peristently.

    def __init__(
        self,
        path: Path,
        expire_after: timedelta,
        parent: Optional[TogglCachedEndpoint] = None,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.session = None

    def commit(self) -> None:
        self.session.save(self.cache_path)

    def save_cache(
        self,
        update: Iterable[TogglClass],
        method: RequestMethod,
    ) -> None:
        self.parent_exists()
        func = self.find_method(method)
        if func is not None:
            func(update)

        self.commit()

    def load_cache(self) -> list[TogglClass]:
        self.parent_exists()
        return self.session.data

    def find_entry(
        self,
        entry: Optional[Mapping | TogglClass] = None,
        **kwargs,
    ) -> Optional[TogglClass]:
        if not self.session.data:
            return None
        for item in self.session.data:
            if entry is not None and item["id"] == entry["id"]:
                return item
        return None

    def add_entry(
        self,
        item: TogglClass,
    ) -> None:
        find_entry = self.find_entry(entry=item)
        if not find_entry:
            return self.session.data.append(item)
        index = self.session.data.index(find_entry)
        self.session.data[index] = item
        return self.commit()

    def add_entries(
        self,
        update: list[TogglClass],
        **kwargs,
    ) -> None:
        if not update:
            return self.session.data
        if isinstance(update, TogglClass):
            return self.add_entry(update)
        for item in update:
            self.add_entry(item)
        return None

    def update_entries(
        self,
        update: list[TogglClass],
        **kwargs,
    ) -> None:
        self.add_entries(update)

    def delete_entry(self, entry: TogglClass) -> None:
        find_entry = self.find_entry(entry)
        if not find_entry:
            return None
        index = self.session.data.index(find_entry)
        self.session.data.pop(index)
        return self.commit()

    def delete_entries(
        self,
        update: list[TogglClass],
        **kwargs,
    ) -> None:
        for entry in update:
            self.delete_entry(entry)
        self.commit()

    @property
    def cache_path(self) -> Path:
        return self._cache_path / f"cache_{self.parent.model.__tablename__}.json"

    @property
    def parent(self) -> TogglCachedEndpoint | None:
        return super().parent

    @parent.setter
    def parent(self, parent: Optional[TogglCachedEndpoint]) -> None:
        self._parent = parent
        if parent is not None and self.session is None:
            self.session = JSONSession()
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
    MATCH_DICT: Final[str, TogglClass] = {
        TogglClass.__tablename__: TogglClass,
        TogglClient.__tablename__: TogglClient,
        TogglProject.__tablename__: TogglProject,
        TogglTag.__tablename__: TogglTag,
        TogglTracker.__tablename__: TogglTracker,
        TogglWorkspace.__tablename__: TogglWorkspace,
    }

    def decode(self, obj: Any) -> Any:
        if obj and isinstance(obj, str):
            with contextlib.suppress(json.decoder.JSONDecodeError):
                obj = super().decode(obj)

        if isinstance(obj, dict) and "timestamp" in obj and isinstance(obj["timestamp"], str):
            obj["timestamp"] = parse_iso(obj["timestamp"])
        if isinstance(obj, dict) and "class" in obj:
            cls: str = obj.pop("class")
            return self.MATCH_DICT[cls].from_kwargs(**obj)

        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = self.decode(v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                obj[i] = self.decode(v)

        return obj
