import pytest

from toggl_api.modules.models import TogglWorkspace


@pytest.mark.unit()
def test_workspace_model():
    data = {
        "id": 1100,
        "name": "test",
    }
    workspace = TogglWorkspace.from_kwargs(**data)
    assert isinstance(workspace, TogglWorkspace)
    assert workspace.id == data["id"]
    assert workspace.name == data["name"]


@pytest.mark.integration()
def test_get_workspace(workspace_object):
    data = workspace_object.get_workspace(refresh=True)
    assert isinstance(data, TogglWorkspace)
    assert data.id == workspace_object.workspace_id
    assert workspace_object.cache.cache_path.exists()
