import pytest

from src.modules.models import TogglClient


@pytest.mark.unit()
def test_client_model(get_workspace_id):
    data = {"id": 1, "name": "Test", "workspace_id": get_workspace_id}
    client = TogglClient.from_kwargs(**data)
    assert isinstance(client, TogglClient)
    assert client.id == data["id"]
    assert client.name == data["name"]
    assert client.workspace.id == get_workspace_id


@pytest.mark.integration()
def test_client_get(client_object, cached_client_object, get_workspace_id):
    name = "test_client_get"

    client = client_object.create_client(name=name)
    assert isinstance(client, TogglClient)
    assert client.name == name

    clients = cached_client_object.get_clients(refresh=True)
    assert len(clients) > 0
    assert any(client.name == name for client in clients)

    client_object.delete_client(clients[0].id)


@pytest.mark.integration()
def test_client_create(client_object, get_workspace_id):
    name = "test_client_create"
    client = client_object.create_client(name=name)
    assert isinstance(client, TogglClient)
    assert client.name == name
    client_object.delete_client(client.id)


@pytest.mark.integration()
def test_client_update(client_object, get_workspace_id):
    name = "test_client_update"
    client = client_object.create_client(name=name)
    assert isinstance(client, TogglClient)
    assert client.name == name

    client = client_object.update_client(client.id, name="test_client_update_2")
    assert isinstance(client, TogglClient)
    assert client.name == name + "_2"

    client_object.delete_client(client.id)
