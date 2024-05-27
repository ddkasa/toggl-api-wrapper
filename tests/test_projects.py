import pytest

from toggl_api.modules.models import TogglProject
from toggl_api.modules.project import ProjectEndpoint


@pytest.fixture(scope="session")
def create_project(project_object, get_workspace_id, faker):
    return project_object.add_project(
        name=faker.name(),
        color=ProjectEndpoint.get_color("blue"),
        active=True,
    )


@pytest.mark.unit()
def test_project_model(get_workspace_id, faker):
    data = {
        "id": 1100,
        "name": faker.name(),
        "workspace": get_workspace_id,
        "color": "#000000",
        "active": True,
    }
    project = TogglProject.from_kwargs(**data)
    assert isinstance(project, TogglProject)
    assert project.id == data["id"]
    assert project.name == data["name"]
    assert project.color == data["color"]
    assert project.workspace == data["workspace"]


@pytest.mark.integration()
def test_create_project(create_project):
    assert isinstance(create_project, TogglProject)
    assert isinstance(create_project.id, int)
    assert create_project.active


@pytest.mark.integration()
def test_get_project(create_project, project_object):
    assert isinstance(create_project, TogglProject)

    check_project = project_object.get_project(create_project.id, refresh=True)
    assert isinstance(check_project, TogglProject)
    assert check_project.name == create_project.name
    assert check_project.color == ProjectEndpoint.get_color("blue")


@pytest.mark.integration()
def test_edit_project(project_object, create_project, faker):
    name = faker.name()
    project = project_object.edit_project(
        create_project,
        name=name,
        color=ProjectEndpoint.get_color("red"),
    )
    assert isinstance(project, TogglProject)
    assert project.name == name
    assert project.color == ProjectEndpoint.get_color("red")
