import pytest

from toggl_api.asyncio import AsyncSqliteCache, async_register_tables


@pytest.fixture
async def setup_async_schema(async_sql_engine):
    return await async_register_tables(async_sql_engine)


@pytest.mark.unit
@pytest.mark.parametrize(
    "table",
    [
        "workspace",
        "client",
        "project",
        "tag",
        "tracker",
        "organization",
    ],
)
def test_create_tables(table, setup_async_schema):
    assert table in setup_async_schema.tables


@pytest.mark.unit
async def test_load_model(async_sqlite_cache, generate_tracker):
    cache = [generate_tracker() for _ in range(5)]
    await async_sqlite_cache.add(*cache)

    assert len(cache) == len(await async_sqlite_cache.load())


@pytest.mark.unit
async def test_add_model(async_sqlite_cache: AsyncSqliteCache, generate_tracker):
    await async_sqlite_cache.add(tracker := generate_tracker())

    assert await async_sqlite_cache.find(tracker.id) is not None


@pytest.mark.unit
async def test_delete_model(async_sqlite_cache: AsyncSqliteCache, generate_tracker):
    await async_sqlite_cache.add(tracker := generate_tracker())
    await async_sqlite_cache.delete(tracker)
    assert await async_sqlite_cache.find(tracker.id) is None


@pytest.mark.unit
async def test_update_model(async_sqlite_cache, generate_tracker, faker):
    await async_sqlite_cache.add(tracker := generate_tracker())

    tracker.name = faker.name()
    await async_sqlite_cache.update(tracker)

    assert (await async_sqlite_cache.find(tracker.id)).name == tracker.name
