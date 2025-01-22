import asyncio

import pytest

from toggl_api.asyncio import AsyncOrganizationEndpoint, AsyncSqliteCache


@pytest.fixture
async def aorg_ep(async_sqlite_cache, config_setup):  # noqa: RUF029
    return AsyncOrganizationEndpoint(config_setup, async_sqlite_cache)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.flaky(rerun_except="httpx.HTTPStatusError", reruns=5)
async def test_org_ep_method_flow(aorg_ep: AsyncOrganizationEndpoint, faker):
    assert isinstance(aorg_ep.cache, AsyncSqliteCache)

    # Test ADD / GET (Cache)
    org = await aorg_ep.add(name := faker.name())
    assert name == org.name

    await asyncio.sleep(20)
    assert (await aorg_ep.get(org.id, refresh=True)) == org

    # Test Edit
    new = await aorg_ep.edit(org, new_name := faker.name())
    assert (found := (await aorg_ep.cache.find(new.id))) is not None
    assert found.name == new_name

    # Test Delete
    await aorg_ep.delete(org.id)
    assert (await aorg_ep.cache.find(new.id)) is None


@pytest.mark.unit
async def test_org_collect_params(aorg_ep: AsyncOrganizationEndpoint, gen_org):
    assert isinstance(aorg_ep.cache, AsyncSqliteCache)

    orgs = [gen_org() for _ in range(5)]
    await aorg_ep.cache.add(*orgs)

    assert len(await aorg_ep.collect()) == len(orgs)
