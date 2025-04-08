import asyncio
from datetime import datetime, timedelta, timezone
from typing import cast

import pytest

from toggl_api import DateTimeError, TogglTracker
from toggl_api.asyncio import AsyncSqliteCache, AsyncTrackerEndpoint


@pytest.fixture
async def atracker_ep(get_workspace_id, async_sqlite_cache, config_setup):  # noqa: RUF029
    return AsyncTrackerEndpoint(get_workspace_id, config_setup, async_sqlite_cache)


@pytest.mark.integration
async def test_tracker_ep_method_flow(gen_tracker_bd, atracker_ep: AsyncTrackerEndpoint, faker):
    assert isinstance(atracker_ep.cache, AsyncSqliteCache)

    # Test ADD / GET (Cache)
    tracker = await atracker_ep.add(bd := gen_tracker_bd())
    assert bd.description == tracker.name
    get = await atracker_ep.get(tracker.id, refresh=True)
    assert isinstance(get, TogglTracker)
    assert get.id == tracker.id
    assert get.name == tracker.name
    assert get.start == tracker.start

    # Test Current
    assert cast("TogglTracker", await atracker_ep.current(refresh=True)).id == tracker.id

    # Test Edit
    bd.description = faker.name()
    new = await atracker_ep.edit(tracker, bd)
    assert (found := (await atracker_ep.cache.find(new.id))) is not None
    assert found.name == bd.description

    # Test Stop
    assert cast("TogglTracker", await atracker_ep.stop(tracker)).id == tracker.id

    # Test Delete
    await atracker_ep.delete(tracker.id)
    assert (await atracker_ep.cache.find(new.id)) is None


@pytest.mark.unit
async def test_get_method(atracker_ep: AsyncTrackerEndpoint, generate_tracker):
    cache = [generate_tracker() for _ in range(5)]
    await cast("AsyncSqliteCache", atracker_ep.cache).add(*cache)

    assert await atracker_ep.get(cache[0].id) is not None


@pytest.mark.unit
async def test_collect_params(atracker_ep: AsyncTrackerEndpoint, generate_tracker):
    start = datetime.now(tz=timezone.utc) - timedelta(minutes=10)

    # Test for datetime edge cases
    with pytest.raises(DateTimeError):
        await atracker_ep.collect(start_date=start, end_date=start - timedelta(days=1))

    with pytest.raises(DateTimeError):
        await atracker_ep.collect(
            start_date=start + timedelta(days=2),
            end_date=start + timedelta(days=2),
        )

    # Add dummy trackers to cache.
    cache = [generate_tracker() for _ in range(5)]
    await cast("AsyncSqliteCache", atracker_ep.cache).add(*cache)

    # Test for filtering
    assert len(await atracker_ep.collect(start_date=start - timedelta(days=3), end_date=start - timedelta(days=2))) == 0
    assert len(await atracker_ep.collect(since=start)) == len(cache)


@pytest.mark.integration
async def test_bulk_edit(atracker_ep: AsyncTrackerEndpoint, gen_tracker_bd):
    tracker = await atracker_ep.add(gen_tracker_bd())

    new_bd = gen_tracker_bd()

    assert tracker.id in (await atracker_ep.bulk_edit(tracker, body=new_bd)).successes

    assert cast("TogglTracker", await atracker_ep.get(tracker, refresh=True)).name == new_bd.description


@pytest.mark.integration
async def test_tracker_collection(atracker_ep: AsyncTrackerEndpoint, add_tracker):
    # NOTE: Make sure tracker object is missing from cache for the refresh.
    assert atracker_ep.cache is not None

    collection = await atracker_ep.collect(refresh=True)
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)

    await asyncio.sleep(1)

    collection = await atracker_ep.collect()
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)


@pytest.mark.integration
async def test_tracker_collection_date(atracker_ep, add_tracker):
    ts = datetime.now(tz=timezone.utc)
    collect = await atracker_ep.collect(
        start_date=ts.replace(hour=(ts.hour - 1) % 24),
        end_date=ts.replace(year=ts.year + 1),
        refresh=True,
    )
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)

    collect = await atracker_ep.collect(
        start_date=ts.replace(hour=(ts.hour - 1) % 24),
        end_date=ts.replace(year=ts.year + 1),
    )
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)
