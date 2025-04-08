from datetime import datetime, timedelta
from typing import cast

import pytest
from httpx import HTTPStatusError

from toggl_api import DateTimeError, TogglWorkspace, WorkspaceBody
from toggl_api.asyncio import AsyncSqliteCache, AsyncWorkspaceEndpoint


@pytest.fixture
async def aworkspace_ep(get_workspace_id, async_sqlite_cache, config_setup):  # noqa: RUF029
    return AsyncWorkspaceEndpoint(get_workspace_id, config_setup, async_sqlite_cache)


@pytest.mark.integration
async def test_workspace_ep_method_flow(aworkspace_ep: AsyncWorkspaceEndpoint, faker, get_workspace_id):
    assert isinstance(aworkspace_ep.cache, AsyncSqliteCache)

    # Test ADD / GET (Cache)
    body = WorkspaceBody(faker.name())

    with pytest.raises(HTTPStatusError):
        await aworkspace_ep.add(body)

    assert cast("TogglWorkspace", await aworkspace_ep.get(get_workspace_id, refresh=True)).id == get_workspace_id


@pytest.mark.unit
async def test_workspace_collect_params(aworkspace_ep: AsyncWorkspaceEndpoint, gen_workspace):
    assert isinstance(aworkspace_ep.cache, AsyncSqliteCache)

    wps = [gen_workspace() for _ in range(5)]
    await aworkspace_ep.cache.add(*wps)

    assert len(await aworkspace_ep.collect()) == len(wps)

    with pytest.raises(DateTimeError):
        await aworkspace_ep.collect(datetime.now().astimezone() + timedelta(hours=1))


@pytest.mark.integration
async def test_workspace_statistics(aworkspace_ep, get_workspace_id, faker):
    stats = await aworkspace_ep.statistics(TogglWorkspace(get_workspace_id, faker.name()))

    assert isinstance(stats, dict)

    assert isinstance(stats["admins"], list)
    assert isinstance(stats["groups_count"], int)
    assert isinstance(stats["members_count"], int)


@pytest.mark.integration
@pytest.mark.xfail(reason="Premium Feature", raises=HTTPStatusError)
async def test_tracker_constraints(aworkspace_ep, get_workspace_id, faker):
    assert isinstance(await aworkspace_ep.tracker_constraints(TogglWorkspace(get_workspace_id, faker.name())), dict)
