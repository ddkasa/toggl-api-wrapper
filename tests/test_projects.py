import pytest

from toggl_api.modules.models import TogglProject
from toggl_api.modules.models.models import TogglWorkspace
from toggl_api.modules.project import ProjectEndpoint


@pytest.fixture()
def create_project(project_object, get_workspace_id):
    project = project_object.add_project(
        name="test_create_project",
        color=ProjectEndpoint.get_color("blue"),
        active=True,
    )
    yield project
    project_object.delete_project(project.id)


@pytest.mark.unit()
def test_project_model(get_workspace_id):
    data = {
        "id": 1100,
        "name": "test",
        "workspace": TogglWorkspace(id=get_workspace_id, name="test_workspace"),
        "color": "#000000",
        "active": True,
    }
    project = TogglProject.from_kwargs(**data)
    assert isinstance(project, TogglProject)
    assert project.id == data["id"]
    assert project.name == data["name"]
    assert project.color == data["color"]
    assert project.workspace.id == data["workspace"].id


@pytest.mark.integration()
def test_create_project(create_project, project_object, cached_project_object):
    assert isinstance(create_project, TogglProject)

    check_project = cached_project_object.get_project(create_project.id)
    assert isinstance(check_project, TogglProject)
    assert check_project.name == create_project.name
    assert check_project.color == ProjectEndpoint.get_color("blue")


@pytest.mark.integration()
def test_edit_project(project_object, create_project):
    project = project_object.edit_project(
        create_project.id,
        name="test_edit_project",
        color=ProjectEndpoint.get_color("red"),
    )
    assert isinstance(project, TogglProject)
    assert project.name == "test_edit_project"
    assert project.color == ProjectEndpoint.get_color("red")
