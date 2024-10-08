from datetime import datetime, timedelta, timezone

import pytest

from toggl_api.models import TogglProject
from toggl_api.project import ProjectBody, ProjectEndpoint
from toggl_api.utility import format_iso


@pytest.mark.unit
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


@pytest.mark.unit
def test_project_body(project_body, get_workspace_id):
    assert isinstance(project_body, ProjectBody)
    formatted = project_body.format("endpoint", workspace_id=get_workspace_id)
    assert formatted["workspace_id"] == get_workspace_id
    assert isinstance(formatted["active"], bool)
    assert isinstance(formatted["is_private"], bool)


@pytest.mark.unit
def test_project_body_dates(project_body, get_workspace_id, monkeypatch):
    monkeypatch.setattr(project_body, "start_date", datetime.now(tz=timezone.utc))
    monkeypatch.setattr(project_body, "end_date", datetime.now(tz=timezone.utc) - timedelta(hours=1))
    formatted = project_body.format("endpoint", workspace_id=get_workspace_id)
    assert formatted["start_date"] == format_iso(project_body.start_date)
    assert formatted.get("end_date") is None
    monkeypatch.setattr(project_body, "end_date", datetime.now(tz=timezone.utc) + timedelta(hours=1))
    formatted = project_body.format("endpoint", workspace_id=get_workspace_id)
    assert formatted["start_date"] == format_iso(project_body.start_date)
    assert formatted["end_date"] == format_iso(project_body.end_date)


@pytest.mark.unit
def test_project_body_client(project_body, get_workspace_id):
    project_body.client_id = 123
    project_body.client_name = "Test Client"
    formatted = project_body.format("endpoint", workspace_id=get_workspace_id)
    assert formatted["client_id"] == project_body.client_id
    assert formatted.get("client_name") is None
    project_body.client_id = None
    formatted = project_body.format("endpoint", workspace_id=get_workspace_id)
    assert formatted.get("client_id") is None
    assert formatted["client_name"] == project_body.client_name


@pytest.mark.integration
def test_create_project(create_project):
    assert isinstance(create_project, TogglProject)
    assert isinstance(create_project.id, int)
    assert create_project.active


@pytest.mark.integration
def test_get_project(create_project, project_object):
    assert isinstance(create_project, TogglProject)

    check_project = project_object.get(create_project.id, refresh=True)
    assert isinstance(check_project, TogglProject)
    assert check_project.name == create_project.name
    assert check_project.color == create_project.color


@pytest.mark.integration
def test_edit_project(project_object, create_project, faker, project_body):
    project_body.name = faker.name()
    project_body.color = ProjectEndpoint.get_color("blue")

    project = project_object.edit(
        create_project,
        project_body,
    )
    assert isinstance(project, TogglProject)
    assert project.name == project_body.name
    assert project.color == project_body.color
