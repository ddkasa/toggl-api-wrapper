import pytest

from toggl_api.modules.models import TogglClient


@pytest.fixture(scope="session")
def create_client(client_object, get_workspace_id):
    return client_object.create_client(name="test_client_create")


@pytest.mark.unit()
def test_client_model(get_workspace_id):
    data = {"id": 1, "name": "Test", "wid": get_workspace_id}
    client = TogglClient.from_kwargs(**data)
    assert isinstance(client, TogglClient)
    assert client.id == data["id"]
    assert client.name == data["name"]
    assert client.workspace == get_workspace_id


@pytest.mark.integration()
@pytest.mark.order(after="test_client_model")
def test_client_get(client_object, get_workspace_id, create_client):
    clients = client_object.get_clients(refresh=True)
    assert len(clients) > 0
    assert any(client.name == create_client.name for client in clients)


@pytest.mark.integration()
@pytest.mark.order(after="test_client_get")
def test_client_create(client_object, get_workspace_id, create_client):
    assert isinstance(create_client, TogglClient)
    assert create_client.name == "test_client_create"


@pytest.mark.integration()
@pytest.mark.order(after="test_client_create")
def test_client_update(client_object, get_workspace_id, create_client):
    client = client_object.update_client(
        create_client.id,
        name=create_client.name + "_2",
    )
    assert isinstance(client, TogglClient)
    assert client.name == create_client.name + "_2"


@pytest.mark.integration()
@pytest.mark.order(after="test_client_update")
def test_client_delete(client_object, get_workspace_id, create_client):
    assert isinstance(create_client, TogglClient)
    client_object.delete_client(create_client)
