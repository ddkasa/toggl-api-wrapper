import sys

import pytest
from httpx import HTTPStatusError

from toggl_api import ClientBody, TogglClient


@pytest.mark.unit
def test_client_model(get_workspace_id):
    data = {"id": 1, "name": "Test", "wid": get_workspace_id}
    client = TogglClient.from_kwargs(**data)
    assert isinstance(client, TogglClient)
    assert client.id == data["id"]
    assert client.name == data["name"]
    assert client.workspace == get_workspace_id


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("active", "active"),
        ("archived", "archived"),
        ("both", "both"),
        ("Random", None),
    ],
)
def test_client_body(status, expected, faker, get_workspace_id):
    body = ClientBody(faker.name(), status, faker.sentence())
    assert isinstance(body, ClientBody)
    data = body.format("endpoint", wid=get_workspace_id)

    assert data["wid"] == get_workspace_id
    assert data["name"] == body.name
    assert data.get("status") == expected
    assert data["notes"] == body.notes


@pytest.mark.unit
def test_client_name(client_object, create_client_body, monkeypatch):
    monkeypatch.setattr(create_client_body, "name", None)
    with pytest.raises(ValueError):  # noqa: PT011
        client_object.add(create_client_body)


@pytest.mark.integration
@pytest.mark.order(after="test_client_model")
@pytest.mark.parametrize(
    ("body"),
    [
        ClientBody("test"),
        ClientBody(status="active"),
        ClientBody(notes="resting"),
    ],
)
def test_client_collect(body, client_object, get_workspace_id, create_client):
    body = ClientBody(create_client.name, "active")

    clients = client_object.collect(body=body, refresh=True)
    assert len(clients) > 0
    assert any(client.name == create_client.name for client in clients)


@pytest.mark.integration
@pytest.mark.order(after="test_client_collect")
def test_client_get(client_object, create_client):
    client = client_object.get(create_client, refresh=True)
    assert isinstance(client, TogglClient)
    assert client.id == create_client.id

    client = client_object.get(create_client)
    assert isinstance(client, TogglClient)
    assert client.id == create_client.id

    client = client_object.get(create_client.id)
    assert isinstance(client, TogglClient)
    assert client.id == create_client.id


@pytest.mark.unit
@pytest.mark.parametrize(
    ("error"),
    [
        pytest.param(
            500,
            marks=pytest.mark.xfail(
                HTTPStatusError,
                reason="Raising any error thats not 200 or 409.",
            ),
        ),
        404,
        200,
    ],
)
def test_client_get_errors(error, client_object, httpx_mock, number):
    httpx_mock.add_response(status_code=error)
    assert client_object.get(number.randint(100, sys.maxsize), refresh=True) is None


@pytest.mark.integration
@pytest.mark.order(after="test_client_get")
def test_client_create(client_object, create_client_body, create_client):
    assert isinstance(create_client, TogglClient)
    assert create_client.name == create_client_body.name


@pytest.mark.integration
@pytest.mark.order(after="test_client_create")
def test_client_update(client_object, create_client_body, create_client, monkeypatch):
    create_client_body.status = "active"
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


@pytest.mark.unit
def test_client_delete_error(httpx_mock, client_object, number):
    httpx_mock.add_response(status_code=450, method="DELETE")
    with pytest.raises(HTTPStatusError):
        client_object.delete(number.randint(100, sys.maxsize))
