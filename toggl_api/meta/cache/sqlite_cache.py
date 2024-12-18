# ruff: noqa: E402

from __future__ import annotations

import atexit
import warnings
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, TypeVar

try:
    import sqlalchemy as db
    from sqlalchemy.orm import Query, Session
except ImportError:
    pass

import contextlib
from collections.abc import Iterable, Sequence

from toggl_api.models import TogglClass
from toggl_api.models.schema import register_tables
from toggl_api.utility import _requires

from .base_cache import Comparison, TogglCache, TogglQuery

if TYPE_CHECKING:
    from pathlib import Path

    from toggl_api.meta import RequestMethod, TogglCachedEndpoint


T = TypeVar("T", bound=TogglClass)


@_requires("sqlalchemy")
class SqliteCache(TogglCache[T]):
    """Class for caching data to a SQLite database.

    Disconnects database on deletion or exit.

    Params:
        expire_after: Time after which the cache should be refreshed.
            If using an integer it will be assumed as seconds.
            If set to None the cache will never expire.
        parent: Parent endpoint that will use the cache. Assigned
            automatically when supplied to a cached endpoint.

    Attributes:
        expire_after: Time after which the cache should be refreshed.
        database: Sqlalchemy database engine.
        metadata: Sqlalchemy metadata.
        session: Sqlalchemy session.

    Methods:
        load_cache: Loads the data from disk and stores it in the data
            attribute. Invalidates any entries older than expire argument.
        query: Querying method that uses SQL to query cached objects.
    """

    __slots__ = (
        "database",
        "metadata",
        "session",
    )

    def __init__(
        self,
        path: Path,
        expire_after: timedelta | int | None = None,
        parent: TogglCachedEndpoint[T] | None = None,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.database = db.create_engine(f"sqlite:///{self.cache_path}")
        self.metadata = register_tables(self.database)

        self.session = Session(self.database)
        atexit.register(self.session.close)

    def commit(self) -> None:
        self.session.commit()

    def save_cache(self, entry: list[T] | T, method: RequestMethod) -> None:
        func = self.find_method(method)
        if func is None:
            return
        func(entry)

    def load_cache(self) -> Query[T]:
        query = self.session.query(self.model)
        if self.expire_after is not None:
            min_ts = datetime.now(timezone.utc) - self.expire_after
            query.filter(self.model.timestamp > min_ts)  # type: ignore[arg-type]
        return query

    def add_entries(self, entry: Iterable[T] | T) -> None:
        if not isinstance(entry, Iterable):
            entry = (entry,)

        for item in entry:
            if self.find_entry(item):
                self.update_entries(item)
                continue
            self.session.add(item)
        self.commit()

    def update_entries(self, entry: Iterable[T] | T) -> None:
        if not isinstance(entry, Iterable):
            entry = (entry,)

        for item in entry:
            self.session.merge(item)
        self.commit()

    def delete_entries(self, entry: Iterable[T] | T) -> None:
        if not isinstance(entry, Iterable):
            entry = (entry,)

        for item in entry:
            if self.find_entry(item):
                self.session.query(
                    self.model,
                ).filter_by(id=item.id).delete()
        self.commit()

    def find_entry(self, query: T | dict[str, Any]) -> T | None:
        if isinstance(query, TogglClass):
            query = {"id": query.id}

        search = self.session.query(self.model)
        if self._expire_after is not None:
            min_ts = datetime.now(timezone.utc) - self._expire_after
            search = search.filter(self.model.timestamp > min_ts)  # type: ignore[arg-type]
        return search.filter_by(**query).first()

    def query(self, *query: TogglQuery, distinct: bool = False) -> Query[T]:
        """Query method for filtering models from cache.

        Filters cached model by set of supplied queries.

        Supports queries with various comparisons with the [Comparison][toggl_api.Comparison]
        enumeration.

        Args:
            query: Any positional argument that is used becomes query argument.
            distinct: Whether to keep equivalent values around.

        Returns:
            A SQLAlchemy query object with parameters filtered.
        """

        search = self.session.query(self.model)
        if isinstance(self.expire_after, timedelta):
            min_ts = datetime.now(timezone.utc) - self.expire_after
            search = search.filter(self.model.timestamp > min_ts)  # type: ignore[arg-type]

        search = self._query_helper(list(query), search)
        if distinct:
            data = [q.key for q in query]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                search = search.distinct(*data).group_by(*data)  # type: ignore[arg-type]
        return search

    def _query_helper(self, query: list[TogglQuery], query_obj: Query[T]) -> Query[T]:
        if query:
            query_obj = self._match_query(query.pop(0), query_obj)
            return self._query_helper(query, query_obj)
        return query_obj

    def _match_query(self, query: TogglQuery, query_obj: Query[T]) -> Query[T]:
        value = getattr(self.parent.model, query.key)  # type: ignore[union-attr]
        if query.comparison == Comparison.EQUAL:
            if isinstance(query.value, Sequence) and not isinstance(query.value, str):
                return query_obj.filter(value.in_(query.value))
            return query_obj.filter(value == query.value)
        if query.comparison == Comparison.LESS_THEN:
            return query_obj.filter(value < query.value)
        if query.comparison == Comparison.LESS_THEN_OR_EQUAL:
            return query_obj.filter(value <= query.value)
        if query.comparison == Comparison.GREATER_THEN:
            return query_obj.filter(value > query.value)
        if query.comparison == Comparison.GREATER_THEN_OR_EQUAL:
            return query_obj.filter(value >= query.value)
        msg = f"{query.comparison} is not implemented!"
        raise NotImplementedError(msg)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "cache.sqlite"

    def __del__(self) -> None:
        with contextlib.suppress(AttributeError, TypeError):
            self.session.close()
