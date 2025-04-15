"""SQLite cache module."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from itertools import chain
from os import PathLike
from typing import TYPE_CHECKING, TypeVar, cast

from sqlalchemy import MetaData, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from toggl_api.models import TogglClass
from toggl_api.models._schema import _create_mappings

from ._async_cache import TogglAsyncCache

if TYPE_CHECKING:
    from os import PathLike
    from pathlib import Path

    from sqlalchemy.sql.expression import ColumnElement

    from ._async_endpoint import TogglAsyncCachedEndpoint


async def async_register_tables(engine: AsyncEngine) -> MetaData:
    """Set up the database with SQLAlchemy models.

    Args:
        engine: The engine to use when registering tables.

    Returns:
        Engine metadata with the table implemented.

    """
    meta = MetaData()

    _create_mappings(meta)

    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    return meta


T = TypeVar("T", bound=TogglClass)


class AsyncSqliteCache(TogglAsyncCache[T]):
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
        echo_db: Turns on database logging for debugging.

    Attributes:
        expire_after: Time after which the cache should be refreshed.
        database: Async database engine that created or can also be supplied.
        metadata: Metadata generated on object construction.

    Methods:
        load: Loads and expires entries from the database.
        add: Adds new entries to the database.
        update: Updates one or multiple existing entries.
        delete: Deletes one or multiple existing entries.
        find: Find an existing entry.
    """

    __slots__ = ("database", "metadata")

    metadata: MetaData

    def __init__(
        self,
        path: Path | PathLike[str],
        expire_after: timedelta | int | None = None,
        parent: TogglAsyncCachedEndpoint[T] | None = None,
        *,
        engine: AsyncEngine | None = None,
        echo_db: bool = False,
    ) -> None:
        super().__init__(path, expire_after, parent)
        self.database = engine = engine or create_async_engine(
            f"sqlite+aiosqlite:///{self.cache_path}",
        )
        self.database.echo = echo_db

        # NOTE: Tests for an existing loop otherwise gets/creates a new one.
        try:
            asyncio.get_running_loop()
            task = asyncio.create_task(async_register_tables(engine))
            task.add_done_callback(
                lambda x: setattr(self, "metadata", x.result()),
            )
        except RuntimeError:
            self.metadata = asyncio.run(async_register_tables(engine))

    async def load(self) -> list[T]:
        """Load data from the database, discarding items if they are past expiration.

        Rather crude load method as it will load all items into memory.

        Returns:
            A flattend list of models from the database.
        """
        stmt = select(self.model)
        if self.expire_after is not None:
            # TODO: Routine that checks for expiration
            # discards instead of ignoring on load.
            min_ts = datetime.now(timezone.utc) - self.expire_after
            stmt = stmt.filter(
                cast("ColumnElement[bool]", self.model.timestamp > min_ts),
            )

        async with AsyncSession(
            self.database,
            expire_on_commit=False,
        ) as session:
            return list(
                chain.from_iterable((await session.execute(stmt)).fetchall()),
            )

    async def add(self, *entries: T) -> None:
        """Add multiple entries to the database."""
        await self.update(*entries)

    async def update(self, *entries: T) -> None:
        """Update entries in the database."""
        async with AsyncSession(
            self.database,
            expire_on_commit=False,
        ) as session:
            for entry in entries:
                await session.merge(entry)
            await session.commit()

    async def delete(self, *entries: T) -> None:
        """Delete multiple entries in the database."""
        async with AsyncSession(
            self.database,
            expire_on_commit=False,
        ) as session:
            for entry in entries:
                if new := await session.get(self.model, entry.id):
                    await session.delete(new)
            await session.commit()

    async def find(self, pk: int) -> T | None:
        """Find a model based on a primary key.

        Args:
            pk: Primary integer key of the model.

        Returns:
            The found model or None if not found.
        """
        async with AsyncSession(
            self.database,
            expire_on_commit=False,
        ) as session:
            return await session.get(self.model, pk)

    @property
    def cache_path(self) -> Path:
        """Full path to the SQLLite database."""
        return super().cache_path / "cache.sqlite"
