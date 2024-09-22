import pytest

from toggl_api.modules.models import TogglWorkspace


@pytest.mark.unit
def test_workspace_model():
    data = {
        "id": 1100,
        "name": "test",
    }
    workspace = TogglWorkspace.from_kwargs(**data)
    assert isinstance(workspace, TogglWorkspace)
    assert workspace.id == data["id"]
    assert workspace.name == data["name"]


@pytest.mark.integration
def test_get_workspace(workspace_object, get_workspace_id):
    data = workspace_object.get(refresh=True)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id
    assert workspace_object.cache.cache_path.exists()

    data = workspace_object.get()
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id
    assert workspace_object.cache.cache_path.exists()

    data = workspace_object.get(get_workspace_id)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id
    assert workspace_object.cache.cache_path.exists()
