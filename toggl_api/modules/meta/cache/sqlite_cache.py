from __future__ import annotations

import atexit
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import sqlalchemy as db
from sqlalchemy.orm import Session

from toggl_api.modules.models import TogglClass, register_tables

from .base_cache import TogglCache

if TYPE_CHECKING:
    from datetime import timedelta
    from pathlib import Path

    from toggl_api.modules.meta import RequestMethod, TogglCachedEndpoint


class SqliteCache(TogglCache):
    """Class for caching data to a Sqlite database.

    Attributes:
        database: Sqlalchemy database engine.
        metadata: Sqlalchemy metadata.
        session: Sqlalchemy session.

    Methods:
        load_cache: Loads the data from disk and stores it in the data attribute.
            Invalidates any entries older than expire argument.

    """

    __slots__ = (
        "database",
        "metadata",
        "session",
    )

    def __init__(
        self,
        path: Path,
        expire_after: timedelta,
        parent: Optional[TogglCachedEndpoint] = None,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.database = db.create_engine(f"sqlite:///{self.cache_path}")
        self.metadata = register_tables(self.database)

        self.session = Session(self.database)
        atexit.register(self.session.close)

    def commit(self) -> None:
        self.session.commit()

    def save_cache(
        self,
        entry: list[TogglClass] | TogglClass,
        method: RequestMethod,
    ) -> None:
        func = self.find_method(method)
        if func is None:
            return
        func(entry)
        self.commit()

    def load_cache(self) -> db.Query[TogglClass]:
        if self.parent is None:
            msg = "Cannot load cache without parent!"
            raise ValueError(msg)
        query = self.session.query(self.parent.model)
        min_ts = datetime.now(timezone.utc) - self._expire_after
        return query.filter(self.parent.model.timestamp > min_ts)  # type: ignore[operator]

    def add_entries(self, entry: list[TogglClass] | TogglClass) -> None:
        if isinstance(entry, TogglClass):
            self.session.add(entry)
        else:
            self.session.add_all(entry)

    def update_entries(self, entry: list[TogglClass] | TogglClass) -> None:
        if isinstance(entry, TogglClass):
            self.session.merge(entry)
        else:
            for item in entry:
                self.session.merge(item)

    def delete_entries(self, entry: list[TogglClass] | TogglClass) -> None:
        if isinstance(entry, TogglClass):
            return self.session.delete(entry)

        for item in entry:
            self.delete_entry(item)
        return None

    def delete_entry(self, entry: TogglClass) -> None:
        self.session.delete(entry)

    def find_entry(
        self,
        query: TogglClass | dict,
    ) -> db.Query[TogglClass]:
        if isinstance(query, TogglClass):
            query = {"name": query.name, "id": query.id}
        if self.parent is None:
            msg = "Cannot load cache without parent!"
            raise ValueError(msg)
        min_ts = datetime.now(timezone.utc) - self.expire_after
        search = self.session.query(self.parent.model)
        search = search.filter(self.parent.model.timestamp >= min_ts)  # type: ignore[operator]
        return search.filter_by(**query)  # type: ignore[name-defined]

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "cache.sqlite"
