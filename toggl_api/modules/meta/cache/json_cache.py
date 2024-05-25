from __future__ import annotations

import contextlib
import json
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


class JSONCache(TogglCache):
    """Class for caching Toggl data to disk in JSON format.

    Args:
        path: Path to the cache file
        expire_after: Time after which the cache should be refreshed
        parent: Parent TogglCachedEndpoint

    """

    def store_cache(self, data: Iterable) -> None:
        data = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "data": data,
            "version": version,
        }
        with self.cache_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, cls=CustomEncoder)

    def save_cache(
        self,
        data: Iterable[TogglClass],
        update: Iterable[TogglClass],
        method: RequestMethod,
    ) -> None:
        self.parent_exists()
        func = self.find_method(method)
        if func is not None:
            data = func(data, update)
        self.store_cache(data)

    def load_cache(self) -> list[TogglClass]:
        self.parent_exists()
        now = datetime.now(tz=timezone.utc)
        if not self.cache_path.exists():
            return []
        with self.cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f, cls=CustomDecoder)
        if now - self.expire_after <= parse_iso(data["timestamp"]):
            return data["data"]

        return []

    def find_entry(
        self,
        data: list[TogglClass],
        *,
        single: int = 1,
        entry: Optional[Mapping | TogglClass] = None,
        **kwargs,
    ) -> list[TogglClass] | TogglClass:
        entries: list[TogglClass] = []
        if not data:
            return entries
        for item in data:
            if item is not None and entry is not None and item["id"] == entry["id"]:
                if single == 1:
                    return [item]
                entries.append(item)
            if single > 1 and len(entries) == single:
                break

        return entries

    def add_entry(
        self,
        data: list[TogglClass],
        update: list[TogglClass],
        **kwargs,
    ) -> list[TogglClass]:
        if not update:
            return data
        for item in update:
            find_entry = self.find_entry(data, entry=item)
            if not find_entry:
                data.append(item)
                continue
            index = data.index(find_entry[0])
            data[index] = item

        return data

    def update_entry(
        self,
        data: list[TogglClass],
        update: list[TogglClass],
        **kwargs,
    ) -> list[TogglClass]:
        return self.add_entry(data, update)

    def delete_entry(
        self,
        data: list[TogglClass],
        update: list[TogglClass],
        **kwargs,
    ) -> list[TogglClass]:
        for item in update:
            find_entry = self.find_entry(data, entry=item)
            if not find_entry:
                data.append(item)
                continue
            index = data.index(find_entry[0])
            data[index] = item

    @property
    def cache_path(self) -> Path:
        return self._cache_path / "cache.json"


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
            return self.MATCH_DICT[cls](**obj)

        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = self.decode(v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                obj[i] = self.decode(v)

        return obj
