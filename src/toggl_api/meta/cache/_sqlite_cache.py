"""SQLite cache module."""

from __future__ import annotations

import atexit
import warnings
from datetime import datetime, timedelta, timezone
from os import PathLike
from typing import TYPE_CHECKING, Any, TypeVar, cast

try:
    import sqlalchemy as db
    from sqlalchemy.orm import Query, Session
except ImportError:
    pass

import contextlib
from collections.abc import Sequence

from toggl_api.models import TogglClass
from toggl_api.models._schema import register_tables
from toggl_api.utility._helpers import _requires

from ._base_cache import Comparison, TogglCache, TogglQuery

if TYPE_CHECKING:
    from os import PathLike
    from pathlib import Path

    from sqlalchemy.engine import Engine
    from sqlalchemy.sql.expression import ColumnElement

    from toggl_api.meta import TogglCachedEndpoint


T = TypeVar("T", bound=TogglClass)


@_requires("sqlalchemy")
class SqliteCache(TogglCache[T]):
    """Class for caching data to a SQLite database.

    Disconnects database on deletion or exit.

    Params:
        path: Where the SQLite database will be stored.
            Ignored if `engine` parameter is not None.
        expire_after: Time after which the cache should be refreshed.
            If using an integer it will be assumed as seconds.
            If set to None the cache will never expire.
        parent: Parent endpoint that will use the cache. Assigned
            automatically when supplied to a cached endpoint.
        engine: Supply an existing database engine or otherwise one is created.
            This may be used to supply an entirely different DB, but SQLite is
            the one that is tested & supported.

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

    __slots__ = ("database", "metadata", "session")

    def __init__(
        self,
        path: Path | PathLike[str],
        expire_after: timedelta | int | None = None,
        parent: TogglCachedEndpoint[T] | None = None,
        *,
        engine: Engine | None = None,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.database = engine or db.create_engine(
            f"sqlite:///{self.cache_path}",
        )
        self.metadata = register_tables(self.database)

        self.session = Session(self.database)
        atexit.register(self.session.close)

    def commit(self) -> None:
        self.session.commit()

    def load(self) -> Query[T]:
        query = self.session.query(self.model)
        if self.expire_after is not None:
            min_ts = datetime.now(timezone.utc) - self.expire_after
            query.filter(
                cast("ColumnElement[bool]", self.model.timestamp > min_ts),
            )
        return query

    def add(self, *entries: T) -> None:
        for item in entries:
            if self.find(item):
                self.update(item)
                continue
            self.session.add(item)
        self.commit()

    def update(self, *entries: T) -> None:
        for item in entries:
            self.session.merge(item)
        self.commit()

    def delete(self, *entries: T) -> None:
        for entry in entries:
            if self.find(entry):
                self.session.query(
                    self.model,
                ).filter_by(id=entry.id).delete()
        self.commit()

    def find(self, query: T | dict[str, Any]) -> T | None:
        if isinstance(query, TogglClass):
            query = {"id": query.id}

        search = self.session.query(self.model)
        if self._expire_after is not None:
            min_ts = datetime.now(timezone.utc) - self._expire_after
            search = search.filter(
                cast("ColumnElement[bool]", self.model.timestamp > min_ts),
            )
        return search.filter_by(**query).first()

    def query(
        self,
        *query: TogglQuery[Any],
        distinct: bool = False,
    ) -> Query[T]:
        """Query method for filtering models from cache.

        Filters cached model by set of supplied queries.

        Supports queries with various comparisons with the [Comparison][toggl_api.meta.cache.Comparison]
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
            search = search.filter(
                cast("ColumnElement[bool]", self.model.timestamp > min_ts),
            )

        search = self._query_helper(list(query), search)
        if distinct:
            data = [q.key for q in query]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                search = search.distinct(*data).group_by(*data)  # type: ignore[arg-type] # FIX: Remove and use selec tobject instead.
        return search

    def _query_helper(
        self,
        query: list[TogglQuery[Any]],
        query_obj: Query[T],
    ) -> Query[T]:
        if query:
            query_obj = self._match_query(query.pop(0), query_obj)
            return self._query_helper(query, query_obj)
        return query_obj

    def _match_query(
        self,
        query: TogglQuery[Any],
        query_obj: Query[T],
    ) -> Query[T]:
        value = getattr(self.model, query.key)
        if query.comparison == Comparison.EQUAL:
            if isinstance(query.value, Sequence) and not isinstance(
                query.value,
                str,
            ):
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
