from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from toggl_api import TogglProject
from toggl_api.asyncio import AsyncProjectEndpoint, AsyncSqliteCache

if TYPE_CHECKING:
    from toggl_api import ProjectBody


@pytest.fixture
async def aproject_ep(get_workspace_id, async_sqlite_cache, config_setup):  # noqa: RUF029
    return AsyncProjectEndpoint(get_workspace_id, config_setup, async_sqlite_cache)


@pytest.mark.integration
async def test_project_ep_method_flow(gen_proj_bd, aproject_ep: AsyncProjectEndpoint, faker):
    assert isinstance(aproject_ep.cache, AsyncSqliteCache)

    # Test ADD / GET (Cache)
    project = await aproject_ep.add(bd := gen_proj_bd())
    assert bd.name == project.name
    assert await aproject_ep.get(project.id, refresh=True) == project

    # Test Edit
    bd.name = faker.name()
    new = await aproject_ep.edit(project, bd)
    assert (found := (await aproject_ep.cache.find(new.id))) is not None
    assert found.name == bd.name

    # Test Delete
    await aproject_ep.delete(project.id)
    assert (await aproject_ep.cache.find(new.id)) is None


@pytest.mark.unit
async def test_project_collect_params(aproject_ep: AsyncProjectEndpoint, gen_project, gen_proj_bd):
    assert isinstance(aproject_ep.cache, AsyncSqliteCache)

    projects = [gen_project() for _ in range(5)]
    await aproject_ep.cache.add(*projects)

    assert len(await aproject_ep.collect()) == len(projects)

    body: ProjectBody = gen_proj_bd()
    body.statuses.append(TogglProject.Status.ARCHIVED)
    assert not (await aproject_ep.collect(body))


@pytest.mark.unit
def test_project_status_to_query():
    statement = select(TogglProject)
    with pytest.raises(NotImplementedError):
        AsyncProjectEndpoint.status_to_query(TogglProject.Status.DELETED, statement)
