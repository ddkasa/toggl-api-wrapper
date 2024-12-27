import pytest

from toggl_api import TogglTracker
from toggl_api.asyncio import AsyncSqliteCache


class DummyEndpoint:
    MODEL = TogglTracker


@pytest.fixture
def async_sqlite_cache(tmp_path):
    return AsyncSqliteCache(tmp_path, parent=DummyEndpoint, echo_db=False)


@pytest.fixture
def async_sql_engine(async_sqlite_cache):
    return async_sqlite_cache.database
