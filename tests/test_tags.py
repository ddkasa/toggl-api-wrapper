import pytest

from src.modules.models import TogglTag


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

    tag_object.delete_tag(tag.id)


@pytest.mark.integration()
def test_tag_update(tag_object, cached_tag_object, get_workspace_id):
    name = "test_tag_update"
    tag = tag_object.create_tag(name)
    assert isinstance(tag, TogglTag)
    assert tag.name == name
    tag = tag_object.update_tag(tag.id, name="test_tag_update_2")
    assert isinstance(tag, TogglTag)
    assert tag.name == name + "_2"

    tag_object.delete_tag(tag.id)


@pytest.mark.integration()
def test_get_tag(tag_object, cached_tag_object, get_workspace_id):
    name = "test_tag_get"
    tag = tag_object.create_tag(name)
    tags = cached_tag_object.get_tags(refresh=True)
    assert len(tags) > 0
    assert any(tag.id == t.id for t in tags)

    tag_object.delete_tag(tag.id)
