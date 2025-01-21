import pytest

from toggl_api import ClientBody, NamingError
from toggl_api.asyncio import AsyncClientEndpoint, AsyncSqliteCache


@pytest.fixture
async def aclient_ep(get_workspace_id, async_sqlite_cache, config_setup):  # noqa: RUF029
    return AsyncClientEndpoint(get_workspace_id, config_setup, async_sqlite_cache)


@pytest.mark.integration
async def test_client_ep_method_flow(aclient_ep: AsyncClientEndpoint, faker):
    assert isinstance(aclient_ep.cache, AsyncSqliteCache)

    with pytest.raises(NamingError):
        await aclient_ep.add(ClientBody())

    body = ClientBody(faker.name())
    # Test ADD / GET (Cache)
    client = await aclient_ep.add(body)
    assert body.name == client.name
    assert await aclient_ep.get(client.id, refresh=True) == client
    assert await aclient_ep.get(client, refresh=False) == client
    # Test Edit
    body.name = faker.name()
    body.status = "archived"
    new = await aclient_ep.edit(client, body)
    assert (found := (await aclient_ep.cache.find(new.id))) is not None
    assert found.name == body.name

    # Test Delete
    await aclient_ep.delete(client.id)
    assert (await aclient_ep.cache.find(new.id)) is None


@pytest.mark.unit
async def test_client_collect_params(aclient_ep: AsyncClientEndpoint, gen_client):
    assert isinstance(aclient_ep.cache, AsyncSqliteCache)

    clients = [gen_client() for _ in range(5)]
    await aclient_ep.cache.add(*clients)

    assert len(await aclient_ep.collect()) == len(clients)

    body = ClientBody(clients[0].name, status="both")
    # NOTE: Possible bug here if two of clients have the same name generated.
    assert len(await aclient_ep.collect(body)) == 1


@pytest.mark.integration
async def test_client_collect(aclient_ep, get_workspace_id, create_client):
    body = ClientBody(create_client.name, "active")

    clients = await aclient_ep.collect(body=body, refresh=True)
    assert len(clients) > 0
    assert any(client.name == create_client.name for client in clients)
