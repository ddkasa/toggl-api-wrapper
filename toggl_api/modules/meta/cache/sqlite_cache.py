from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import sqlalchemy as db
from sqlalchemy.orm import Session

from toggl_api.modules.models import register_tables

from .base_cache import TogglCache

if TYPE_CHECKING:
    from datetime import timedelta
    from pathlib import Path

    from toggl_api.modules.meta import RequestMethod, TogglCachedEndpoint
    from toggl_api.modules.models import TogglClass


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

    def save_cache(self, data: TogglClass, method: RequestMethod) -> None:
        func = self.find_method(method)
        if func is None:
            msg = f"Caching method {method} is not implemented"
            raise NotImplementedError(msg)

        func(data)

    def load_cache(self) -> list[TogglClass]:
        self.parent_exists()

        return []

    def add_entry(self, entry: TogglClass) -> None:
        if self.parent is None:
            return
        with Session(self.database) as session:
            session.add(entry)
            session.commit()

    def update_entry(self, entry: TogglClass) -> None:
        with Session(self.database) as session:
            session.add(entry)
            session.commit()

    def delete_entry(self, entry: TogglClass) -> None:
        with Session(self.database) as session:
            session.delete(entry)
            session.commit()

    def find_entry(  # type: ignore[override]
        self,
        query: TogglClass,
    ) -> TogglClass | None:
        if self.parent is None:
            return None
        with Session(self.database) as session:
            return session.query(self.parent.model).get(query)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "cache.sqlite"
