import pytest

from toggl_api.asyncio import AsyncSqliteCache, AsyncTagEndpoint


@pytest.fixture
async def atag_ep(get_workspace_id, async_sqlite_cache, config_setup):  # noqa: RUF029
    return AsyncTagEndpoint(get_workspace_id, config_setup, async_sqlite_cache)


@pytest.mark.integration
async def test_tag_ep_method_flow(atag_ep: AsyncTagEndpoint, faker):
    assert isinstance(atag_ep.cache, AsyncSqliteCache)

    # Test ADD / GET (Cache)
    tag = await atag_ep.add(name := faker.name())
    assert name == tag.name
    assert await atag_ep.get(tag, refresh=True) == tag

    # Test Edit
    new = await atag_ep.edit(tag, new_name := faker.name())
    assert (found := (await atag_ep.cache.find(new.id))) is not None
    assert found.name == new_name

    # Test Delete
    await atag_ep.delete(tag.id)
    assert (await atag_ep.cache.find(new.id)) is None


@pytest.mark.unit
async def test_tag_collect_params(atag_ep: AsyncTagEndpoint, gen_tag):
    assert isinstance(atag_ep.cache, AsyncSqliteCache)

    tags = [gen_tag() for _ in range(5)]
    await atag_ep.cache.add(*tags)

    assert len(await atag_ep.collect()) == len(tags)
