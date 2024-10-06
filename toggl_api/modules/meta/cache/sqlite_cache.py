from __future__ import annotations

import atexit
import warnings
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

import sqlalchemy as db
from sqlalchemy.orm import Query, Session

from toggl_api.modules.models import TogglClass, register_tables

from .base_cache import TogglCache

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from toggl_api.modules.meta import RequestMethod, TogglCachedEndpoint


class SqliteCache(TogglCache):
    """Class for caching data to a Sqlite database.

    Args:
        expire_after: Time after which the cache should be refreshed.
            If using an integer it will be assumed as seconds.
            If set to None the cache will never expire.
        parent: Parent endpoint that will use the cache. Usually assigned
            automatically when supplied to a cached endpoint.

    Attributes:
        database: Sqlalchemy database engine.
        metadata: Sqlalchemy metadata.
        session: Sqlalchemy session.

    Methods:
        load_cache: Loads the data from disk and stores it in the data
            attribute. Invalidates any entries older than expire argument.

    """

    __slots__ = (
        "database",
        "metadata",
        "session",
    )

    def __init__(
        self,
        path: Path,
        expire_after: Optional[timedelta | int] = None,
        parent: Optional[TogglCachedEndpoint] = None,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.database = db.create_engine(f"sqlite:///{self.cache_path}")
        self.metadata = register_tables(self.database)

        self.session = Session(self.database)
        atexit.register(self.session.close)

        warnings.warn(
            "SQLAlchemy will become an optional dependency in v1.0.0",
            DeprecationWarning,
            stacklevel=2,
        )

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

    def load_cache(self) -> Query[TogglClass]:
        if self.parent is None:
            msg = "Cannot load cache without parent!"
            raise ValueError(msg)
        query = self.session.query(self.parent.model)
        if self.expire_after is not None:
            min_ts = datetime.now(timezone.utc) - self._expire_after  # type: ignore[operator]
            query.filter(self.parent.model.timestamp > min_ts)  # type: ignore[operator]
        return query

    def add_entries(self, entry: Iterable[TogglClass] | TogglClass) -> None:
        if isinstance(entry, TogglClass):
            entry = (entry,)
        for item in entry:
            if self.find_entry(item):
                self.update_entries(item)
                continue
            self.session.add(item)
        self.commit()

    def update_entries(self, entry: Iterable[TogglClass] | TogglClass) -> None:
        if isinstance(entry, TogglClass):
            entry = (entry,)

        for item in entry:
            self.session.merge(item)
        self.commit()

    def delete_entries(self, entry: Iterable[TogglClass] | TogglClass) -> None:
        if isinstance(entry, TogglClass):
            entry = (entry,)

        for item in entry:
            if self.find_entry(item):
                self.session.query(
                    self.parent.model,  # type: ignore[union-attr]
                ).filter_by(id=item.id).delete()
        self.commit()

    def find_entry(self, query: TogglClass | dict) -> TogglClass | None:
        if self.parent is None:
            msg = "Cannot load cache without parent!"
            raise ValueError(msg)

        if isinstance(query, TogglClass):
            query = {"id": query.id}

        search = self.session.query(self.parent.model)
        if self._expire_after is not None:
            min_ts = datetime.now(timezone.utc) - self._expire_after
            search = search.filter(self.parent.model.timestamp > min_ts)  # type: ignore[operator]
        return search.filter_by(**query).first()  # type: ignore[name-defined]

    def query(
        self,
        *,
        inverse: bool = False,
        distinct: bool = False,
        **query: dict[str, Any],
    ) -> Query[TogglClass]:
        if self.parent is None:
            msg = "Cannot load cache without parent!"
            raise ValueError(msg)

        search = self.session.query(self.parent.model)
        if isinstance(self.expire_after, timedelta):
            min_ts = datetime.now(timezone.utc) - self._expire_after  # type: ignore[operator]
            search = search.filter(self.parent.model.timestamp > min_ts)  # type: ignore[operator]
        return search.filter_by(**query)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "cache.sqlite"

    def __del__(self) -> None:
        self.session.close()
