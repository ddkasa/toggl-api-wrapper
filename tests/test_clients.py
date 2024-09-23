import pytest

from toggl_api import ClientBody, TogglClient


@pytest.fixture
def create_client_body(get_workspace_id, faker):
    return ClientBody(name=faker.name(), workspace_id=get_workspace_id)


@pytest.fixture
def create_client(client_object, create_client_body):
    return client_object.add(create_client_body)


@pytest.mark.unit
def test_client_model(get_workspace_id):
    data = {"id": 1, "name": "Test", "wid": get_workspace_id}
    client = TogglClient.from_kwargs(**data)
    assert isinstance(client, TogglClient)
    assert client.id == data["id"]
    assert client.name == data["name"]
    assert client.workspace == get_workspace_id


@pytest.mark.unit
def test_client_body(create_client_body, faker):
    assert isinstance(create_client_body, ClientBody)
    create_client_body.status = faker.name()
    create_client_body.notes = faker.name()
    data = create_client_body.format(create_client_body.workspace_id)

    assert data["status"] == create_client_body.status
    assert data["notes"] == create_client_body.notes


@pytest.mark.unit
def test_client_name(client_object, create_client_body, monkeypatch):
    monkeypatch.setattr(create_client_body, "name", None)
    with pytest.raises(ValueError):  # noqa: PT011
        client_object.add(create_client_body)


@pytest.mark.integration
@pytest.mark.order(after="test_client_model")
def test_gets(client_object, get_workspace_id, create_client):
    clients = client_object.collect(refresh=False)
    assert len(clients) > 0
    assert any(client.name == create_client.name for client in clients)
    clients = client_object.collect(refresh=True)
    assert len(clients) > 0
    assert any(client.name == create_client.name for client in clients)


@pytest.mark.integration
@pytest.mark.order(after="test_gets")
def test_get(client_object, get_workspace_id, create_client):
    client = client_object.get(create_client)
    assert isinstance(client, TogglClient)
    assert client.id == create_client.id

    client = client_object.get(create_client.id)
    assert isinstance(client, TogglClient)
    assert client.id == create_client.id

    client = client_object.get(create_client, refresh=True)
    assert isinstance(client, TogglClient)
    assert client.id == create_client.id


@pytest.mark.integration
@pytest.mark.order(after="test_client_get")
def test_client_create(client_object, create_client_body, create_client):
    assert isinstance(create_client, TogglClient)
    assert create_client.name == create_client_body.name


@pytest.mark.integration
@pytest.mark.order(after="test_client_create")
def test_client_update(client_object, create_client_body, create_client, monkeypatch):
    monkeypatch.setattr(create_client_body, "name", create_client_body.name + "_2")
    client = client_object.edit(create_client, body=create_client_body)
    assert isinstance(client, TogglClient)
    assert client.name == create_client_body.name


@pytest.mark.integration
@pytest.mark.order(after="test_client_update")
def test_client_delete(client_object, get_workspace_id, create_client):
    assert isinstance(create_client, TogglClient)
    client_object.delete(create_client)


@pytest.mark.integration
@pytest.mark.order(after="test_client_delete")
def test_client_delete_id(client_object, get_workspace_id, create_client):
    assert isinstance(create_client, TogglClient)
    client_object.delete(create_client.id)
