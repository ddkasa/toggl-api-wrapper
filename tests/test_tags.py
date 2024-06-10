import pytest

from toggl_api.modules.models import TogglTag


@pytest.fixture(scope="session")
def add_tag(tag_object):
    return tag_object.create_tag(name="test_tag")


@pytest.mark.unit()
def test_tag_model(get_workspace_id):
    data = {"id": 1, "name": "Test", "workspace_id": get_workspace_id}
    tag = TogglTag.from_kwargs(**data)
    assert isinstance(tag, TogglTag)
    assert tag.id == data["id"]
    assert tag.name == data["name"]


@pytest.mark.integration()
def test_tag_creation(tag_object, get_workspace_id):
    name = "test_tag_creation"
    tag = tag_object.create_tag(name)
    assert isinstance(tag, TogglTag)
    assert tag.name == name


@pytest.mark.integration()
def test_tag_update(tag_object, get_workspace_id, add_tag, monkeypatch):
    monkeypatch.setattr(add_tag, "name", "test_tag_update_2")
    tag = tag_object.update_tag(add_tag)
    assert isinstance(tag, TogglTag)
    assert tag.name == add_tag.name


@pytest.mark.integration()
def test_get_tag(tag_object, get_workspace_id, add_tag):
    tags = tag_object.get_tags(refresh=True)
    assert len(tags) > 0
    assert any(add_tag.id == t.id for t in tags)


@pytest.mark.integration()
def test_delete_tag(tag_object, add_tag):
    tag_object.delete_tag(add_tag)
