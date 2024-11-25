import sys
from datetime import datetime, timedelta, timezone

import pytest
from httpx import HTTPStatusError, codes

from toggl_api.models import TogglProject
from toggl_api.project import ProjectBody, ProjectEndpoint
from toggl_api.utility import format_iso


@pytest.fixture
def project_sample(faker, number, get_workspace_id):
    return {
        "id": number.randint(100, sys.maxsize),
        "name": faker.name(),
        "workspace": get_workspace_id,
        "color": ProjectEndpoint.get_color(""),
        "active": True,
    }


@pytest.mark.unit
def test_project_model(get_workspace_id, faker, project_sample):
    project = TogglProject.from_kwargs(**project_sample)
    assert isinstance(project, TogglProject)
    assert project.id == project_sample["id"]
    assert project.name == project_sample["name"]
    assert project.color == project_sample["color"]
    assert project.workspace == project_sample["workspace"]


@pytest.mark.unit
def test_project_body(project_body, get_workspace_id):
    assert isinstance(project_body, ProjectBody)
    formatted = project_body.format("endpoint", workspace_id=get_workspace_id)
    assert formatted["workspace_id"] == get_workspace_id
    assert isinstance(formatted["active"], bool)
    assert isinstance(formatted["is_private"], bool)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (TogglProject.Status.ARCHIVED, {"active"}),
        (TogglProject.Status.UPCOMING, {"start_date"}),
        (TogglProject.Status.ENDED, {"end_date"}),
        pytest.param(
            TogglProject.Status.ACTIVE,
            {"active", "start_date", "end_date"},
            marks=pytest.mark.xfail(
                reason="Active project querying is currently not supported!",
                raises=NotImplementedError,
            ),
        ),
        pytest.param(
            TogglProject.Status.DELETED,
            set(),
            marks=pytest.mark.xfail(
                reason="Deleted project querying is currently not supported!",
                raises=NotImplementedError,
            ),
        ),
    ],
)
def test_project_status_query(status, expected):
    assert all(q.key in expected for q in ProjectEndpoint.status_to_query(status))


@pytest.mark.unit
def test_project_body_collect_params(get_workspace_id):
    body = ProjectBody(
        since=datetime.now(timezone.utc),
        user_ids=[12, 21312312],
        client_ids=[21321321],
        group_ids=[213123123],
        statuses=[TogglProject.Status.ACTIVE],
    )
    formatted = body.format("collect", workspace_id=get_workspace_id)
    assert formatted["workspace_id"] == get_workspace_id
    assert isinstance(formatted["since"], int)
    assert isinstance(formatted["user_ids"], list)
    assert isinstance(formatted["client_ids"], list)
    assert isinstance(formatted["group_ids"], list)
    assert "active" in formatted["statuses"]

    formatted = body.format("add", workspace_id=get_workspace_id)
    assert formatted.get("client_ids") is None


@pytest.mark.unit
def test_project_body_dates(project_body, get_workspace_id, monkeypatch):
    monkeypatch.setattr(project_body, "start_date", datetime.now(tz=timezone.utc))
    monkeypatch.setattr(project_body, "end_date", datetime.now(tz=timezone.utc) - timedelta(hours=1))
    formatted = project_body.format("edit", workspace_id=get_workspace_id)
    assert formatted["start_date"] == format_iso(project_body.start_date)
    assert formatted.get("end_date") is None
    monkeypatch.setattr(project_body, "end_date", datetime.now(tz=timezone.utc) + timedelta(hours=1))
    formatted = project_body.format("add", workspace_id=get_workspace_id)
    assert formatted["start_date"] == format_iso(project_body.start_date)
    assert formatted["end_date"] == format_iso(project_body.end_date)

    monkeypatch.setattr(project_body, "start_date", None)
    assert isinstance(project_body.format("edit")["end_date"], str)


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


@pytest.mark.unit
def test_project_name_validation(project_object):
    body = ProjectBody()
    with pytest.raises(
        ValueError,
        match="Name must be set in order to create a project!",
    ):
        project_object.add(body)


@pytest.mark.integration
def test_get_project(create_project, project_object):
    assert isinstance(create_project, TogglProject)

    check_project = project_object.get(create_project.id, refresh=True)
    assert isinstance(check_project, TogglProject)
    assert check_project.name == create_project.name
    assert check_project.color == create_project.color

    check_project = project_object.get(create_project)
    assert isinstance(check_project, TogglProject)
    assert check_project.name == create_project.name
    assert check_project.color == create_project.color


@pytest.mark.unit
def test_get_project_raise(project_object, httpx_mock, number):
    httpx_mock.add_response(status_code=450)
    with pytest.raises(HTTPStatusError):
        project_object.get(number.randint(50, sys.maxsize), refresh=True)

    httpx_mock.add_response(status_code=codes.NOT_FOUND)
    assert project_object.get(number.randint(50, sys.maxsize), refresh=True) is None


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


@pytest.mark.integration
def test_delete_project_id(create_project, project_object):
    assert isinstance(create_project, TogglProject)
    project_object.delete(create_project.id)
    assert project_object.get(create_project.id) is None


@pytest.mark.integration
def test_delete_project_model(create_project, project_object):
    assert isinstance(create_project, TogglProject)
    project_object.delete(create_project)
    assert project_object.get(create_project) is None


@pytest.mark.unit
def test_delete_project_raise(httpx_mock, project_object, number):
    httpx_mock.add_response(status_code=codes.NOT_FOUND)
    assert project_object.delete(number.randint(1, sys.maxsize)) is None

    httpx_mock.add_response(status_code=450)
    with pytest.raises(HTTPStatusError):
        assert project_object.delete(number.randint(1, sys.maxsize)) is None


@pytest.mark.unit
def test_get_color_id():
    for i, key in enumerate(ProjectEndpoint.BASIC_COLORS.values()):
        assert i == ProjectEndpoint.get_color_id(key)
