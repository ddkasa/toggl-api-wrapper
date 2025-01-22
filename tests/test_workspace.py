import pytest
from httpx import HTTPStatusError

from toggl_api import WorkspaceBody
from toggl_api.models import TogglWorkspace


@pytest.fixture
def get_workspace_model(get_workspace_id, faker):
    data = {
        "id": get_workspace_id,
        "name": "test_workspace",
    }
    return TogglWorkspace.from_kwargs(**data)


@pytest.mark.unit
def test_workspace_body(get_workspace_id, faker):
    body = WorkspaceBody(faker.name())

    formatted_body = body.format("add")
    assert formatted_body["name"] == body.name.replace(" ", "-")


@pytest.mark.unit
def test_workspace_model(get_workspace_model, get_workspace_id):
    assert isinstance(get_workspace_model, TogglWorkspace)
    assert get_workspace_model.id == get_workspace_id
    assert get_workspace_model.name == "test_workspace"


@pytest.mark.integration
@pytest.mark.dependency
def test_get_workspace(workspace_object, get_workspace_id, get_workspace_model, request):
    data = workspace_object.get(get_workspace_id, refresh=True)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id
    assert workspace_object.cache.cache_path.exists()

    data = workspace_object.get(get_workspace_id)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id

    data = workspace_object.get(get_workspace_model)
    assert isinstance(data, TogglWorkspace)
    assert data.id == get_workspace_id
    request.config.cache.set("workspace", {"name": data.name, "id": data.id})


@pytest.mark.integration
@pytest.mark.xfail(reason="Enterprise Feature", raises=HTTPStatusError)
def test_add_workspace(workspace_object, number, faker, request, organization_id):
    body = WorkspaceBody(faker.name())
    workspace = workspace_object.add(body)

    if isinstance(workspace, TogglWorkspace):  # pragma: no cover
        assert workspace.name == body.name
        request.config.cache.set("workspace", workspace)


@pytest.mark.integration
@pytest.mark.dependency(dependent=["test_get_workspace"])
def test_edit_workspace(workspace_object, number, faker, request, get_workspace_id):
    wdata = request.config.cache.get("workspace", {})
    body = WorkspaceBody(faker.name())
    workspace = workspace_object.edit(wdata["id"], body)
    assert workspace.name == body.name
    assert workspace.name != wdata["name"]
    body.name = faker.name()
    workspace = workspace_object.edit(workspace, body)
    assert workspace.name == body.name.replace(" ", "-")
    assert workspace.name != wdata["name"]


@pytest.mark.integration
@pytest.mark.xfail(reason="Premium Feature", raises=HTTPStatusError)
def test_tracker_constraints(workspace_object, get_workspace_id, faker):
    workspace_object.tracker_constraints(TogglWorkspace(get_workspace_id, faker.name()))


@pytest.mark.integration
def test_workspace_statistics(workspace_object, get_workspace_id, faker):
    stats = workspace_object.statistics(TogglWorkspace(get_workspace_id, faker.name()))

    assert isinstance(stats, dict)

    assert isinstance(stats["admins"], list)
    assert isinstance(stats["groups_count"], int)
    assert isinstance(stats["members_count"], int)


@pytest.mark.integration
def test_collect_workspace(workspace_object):
    workspaces = workspace_object.collect(refresh=True)
    assert len(workspaces)
    assert all(isinstance(w, TogglWorkspace) for w in workspaces)
