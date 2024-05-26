import pytest

from toggl_api.modules.models import TogglClient


@pytest.fixture()
def create_client(client_object, get_workspace_id):
    name = "test_client_create"
    client = client_object.create_client(name=name)
    yield client
    client_object.delete_client(client.id)


@pytest.mark.unit()
def test_client_model(get_workspace_id):
    data = {"id": 1, "name": "Test", "wid": get_workspace_id}
    client = TogglClient.from_kwargs(**data)
    assert isinstance(client, TogglClient)
    assert client.id == data["id"]
    assert client.name == data["name"]
    assert client.workspace == get_workspace_id


@pytest.mark.integration()
def test_client_delete(client_object, get_workspace_id):
    name = "test_client_delete"
    client = client_object.create_client(name=name)
    assert isinstance(client, TogglClient)
    assert client.name == name
    assert client.workspace == get_workspace_id

    client_object.delete_client(client.id)


@pytest.mark.integration()
def test_client_get(client_object, get_workspace_id, create_client):
    clients = client_object.get_clients(refresh=True)
    assert len(clients) > 0
    assert any(client.name == create_client.name for client in clients)


@pytest.mark.integration()
def test_client_create(client_object, get_workspace_id):
    name = "test_client_create"
    client = client_object.create_client(name=name)
    assert isinstance(client, TogglClient)
    assert client.name == name
    client_object.delete_client(client.id)


@pytest.mark.integration()
def test_client_update(client_object, get_workspace_id, create_client):
    client = client_object.update_client(
        create_client.id,
        name=create_client.name + "_2",
    )
    assert isinstance(client, TogglClient)
    assert client.name == create_client.name + "_2"
