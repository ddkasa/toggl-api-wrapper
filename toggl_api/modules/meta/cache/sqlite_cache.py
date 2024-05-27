from __future__ import annotations

import atexit
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

    def save_cache(self, entry: TogglClass, method: RequestMethod) -> None:
        self.parent_exists()
        func = self.find_method(method)
        if func is None:
            return

        func(entry)

    def load_cache(self) -> list[TogglClass]:
        self.parent_exists()
        return self.session.query(self.parent.model)

    def add_entries(self, entry: TogglClass) -> None:
        if isinstance(entry, TogglClass):
            self.session.add(entry)
        else:
            self.session.add_all(entry)

        self.session.commit()

    def update_entries(self, entry: TogglClass) -> None:
        self.session.merge(entry)
        self.session.commit()

    def delete_entries(self, entry: list[TogglClass]) -> None:
        for item in entry:
            self.delete_entry(item)

    def delete_entry(self, entry: TogglClass) -> None:
        self.session.delete(entry)
        self.session.commit()

    def find_entry(  # type: ignore[override]
        self,
        query: TogglClass,
    ) -> TogglClass | None:
        return self.session.query(self.parent.model).get(query)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "cache.sqlite"
