import httpx
import pytest

from src.modules.models import TogglProject


@pytest.mark.unit()
def test_project_model(get_workspace_id):
    data = {
        "id": 1100,
        "name": "test",
        "workspace_id": get_workspace_id,
        "color": "#000000",
        "active": True,
    }
    project = TogglProject.from_kwargs(**data)
    assert isinstance(project, TogglProject)
    assert project.id == data["id"]
    assert project.name == data["name"]
    assert project.color == data["color"]


@pytest.mark.integration()
def test_create_project(project_object, cached_project_object):
    name = "test_create_project"
    color = "#d94182"
    active = True
    project = project_object.add_project(
        name=name,
        color=color,
        active=active,
    )
    assert isinstance(project, TogglProject)
    assert project.name == name
    assert project.color == color
    assert project.active == active

    check_project = cached_project_object.get_project(project.id)
    assert isinstance(check_project, TogglProject)
    assert check_project.name == project.name
    assert check_project.color == color

    project_object.delete_project(project.id)
