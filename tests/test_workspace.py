import pytest

from toggl_api.models import TogglWorkspace


@pytest.fixture
def get_workspace_model(get_workspace_id, faker):
    data = {
        "id": get_workspace_id,
        "name": "test_workspace",
    }
    return TogglWorkspace.from_kwargs(**data)


@pytest.mark.unit
def test_workspace_model(get_workspace_model, get_workspace_id):
    assert isinstance(get_workspace_model, TogglWorkspace)
    assert get_workspace_model.id == get_workspace_id
    assert get_workspace_model.name == "test_workspace"


@pytest.mark.integration
def test_get_workspace(workspace_object, get_workspace_id, get_workspace_model):
    data = workspace_object.get(refresh=True)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id
    assert workspace_object.cache.cache_path.exists()

    data = workspace_object.get()
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id

    data = workspace_object.get(get_workspace_id)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id

    data = workspace_object.get(get_workspace_model)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id
