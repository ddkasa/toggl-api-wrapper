import sys

import pytest
from httpx import HTTPStatusError

from toggl_api import NamingError, TogglTag


@pytest.fixture
def add_tag(tag_object, faker):
    return tag_object.add(name=faker.name())


@pytest.mark.unit
def test_tag_model(get_workspace_id, faker):
    data = {"id": 1, "name": faker.name(), "workspace_id": get_workspace_id}
    tag = TogglTag.from_kwargs(**data)
    assert isinstance(tag, TogglTag)
    assert tag.id == data["id"]
    assert tag.name == data["name"]


@pytest.mark.integration
def test_tag_creation(tag_object, get_workspace_id, faker):
    name = faker.name()
    tag = tag_object.add(name)
    assert isinstance(tag, TogglTag)
    assert tag.name == name


@pytest.mark.unit
def test_tag_creation_name(tag_object, get_workspace_id, faker):
    name = ""
    with pytest.raises(NamingError):
        assert tag_object.add(name)


@pytest.mark.integration
def test_tag_update(tag_object, get_workspace_id, add_tag, monkeypatch, faker):
    tag = tag_object.edit(add_tag, (name := faker.name()))
    assert isinstance(tag, TogglTag)
    assert tag.name == name


@pytest.mark.unit
def test_tag_edit_name(tag_object, get_workspace_id, faker, number):
    name = ""
    with pytest.raises(NamingError):
        assert tag_object.edit(number.randint(50, 50000), name)


@pytest.mark.integration
def test_get_tag(tag_object, get_workspace_id, add_tag):
    tags = tag_object.collect(refresh=True)
    assert len(tags) > 0
    assert any(add_tag.id == t.id for t in tags)


@pytest.mark.integration
def test_delete_tag(tag_object, add_tag):
    tag_object.delete(add_tag)


@pytest.mark.integration
def test_delete_tag_int(tag_object, add_tag):
    assert tag_object.delete(add_tag.id) is None

    assert tag_object.delete(add_tag.id) is None


@pytest.mark.unit
def test_delete_tag_raise(tag_object, number, httpx_mock):
    httpx_mock.add_response(status_code=450)
    with pytest.raises(HTTPStatusError):
        assert tag_object.delete(number.randint(10, sys.maxsize)) is None


@pytest.mark.integration
def test_tag_get(tag_object, number, httpx_mock, faker):
    httpx_mock.add_response(
        json=(
            json := {
                "id": number.randint(100, sys.maxsize),
                "name": faker.name(),
                "workspace_id": tag_object.workspace_id,
            }
        ),
        status_code=200,
    )
    tag = tag_object.get(json["id"], refresh=True)
    assert tag.id == json["id"]
    assert tag.name == json["name"]
    assert tag.workspace == json["workspace_id"]
