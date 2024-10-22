# mypy: disable-error-code=override

import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import BasicAuth

from scripts.utils import cleanup
from toggl_api.client import ClientEndpoint
from toggl_api.config import generate_authentication
from toggl_api.meta import JSONCache, TogglCachedEndpoint
from toggl_api.meta.cache.sqlite_cache import SqliteCache
from toggl_api.models import TogglClass, TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace
from toggl_api.project import ProjectBody, ProjectEndpoint
from toggl_api.tag import TagEndpoint
from toggl_api.tracker import TrackerBody, TrackerEndpoint
from toggl_api.user import UserEndpoint
from toggl_api.workspace import WorkspaceEndpoint


@pytest.fixture(autouse=True)
def _rate_limit(request):
    yield
    if "integration" in request.keywords:
        time.sleep(1)


@pytest.fixture(scope="session")
def faker():
    return Faker()


@pytest.fixture(scope="session")
def number():
    return random.Random()


@pytest.fixture(scope="session")
def config_setup() -> BasicAuth:
    return generate_authentication()


@pytest.fixture
def get_sqlite_cache(tmp_path):
    return SqliteCache(tmp_path, timedelta(days=1))


@pytest.fixture
def get_json_cache(tmp_path):
    return JSONCache(tmp_path, timedelta(days=1))


@pytest.fixture(scope="session")
def get_workspace_id() -> int:
    return int(os.getenv("TOGGL_WORKSPACE_ID", "0"))


@pytest.fixture
def workspace_object(get_workspace_id, config_setup, get_json_cache):
    return WorkspaceEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture
def project_object(get_workspace_id, config_setup, get_json_cache):
    return ProjectEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture
def user_object(get_workspace_id, config_setup, get_json_cache) -> UserEndpoint:
    return UserEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture
def tracker_object(get_workspace_id, config_setup, get_json_cache, user_object):
    return TrackerEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture
def tracker_object_sqlite(
    get_workspace_id,
    config_setup,
    get_sqlite_cache,
    user_object,
):
    return TrackerEndpoint(get_workspace_id, config_setup, get_sqlite_cache)


@pytest.fixture
def add_tracker(tracker_object, faker):
    body = TrackerBody(
        description=faker.name(),
        start=datetime.now(tz=timezone.utc),
    )
    tracker = tracker_object.add(body=body)
    yield tracker
    tracker_object.delete(tracker)


@pytest.fixture
def client_object(get_json_cache, get_workspace_id, config_setup):
    return ClientEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture
def tag_object(get_workspace_id, config_setup, get_json_cache):
    return TagEndpoint(get_workspace_id, config_setup, get_json_cache)


class ModelTest(TogglClass):
    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglClass:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
        )


class EndPointTest(TogglCachedEndpoint):
    @property
    def endpoint(self) -> str:
        return ""

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker


@pytest.fixture
def meta_object(config_setup, get_workspace_id, get_json_cache):
    return EndPointTest(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture
def meta_object_sqlite(config_setup, get_workspace_id, get_sqlite_cache):
    return EndPointTest(get_workspace_id, config_setup, get_sqlite_cache)


def pytest_sessionstart(session: pytest.Session):
    marks = session.config.getoption("-m", default="")
    if not marks or "integration" in marks:
        cleanup()


def pytest_sessionfinish(session, exitstatus):
    marks = session.config.getoption("-m", default="")
    if not marks or "integration" in marks:
        cleanup()


@pytest.fixture
def model_data(get_workspace_id, faker):
    workspace = TogglWorkspace(get_workspace_id, "test_workspace")

    client = TogglClient(
        id=1,
        name=faker.name(),
        workspace=workspace.id,
    )
    project = TogglProject(
        id=1,
        name=faker.name(),
        workspace=workspace.id,
        color="000000",
        client=client.id,
        active=True,
    )
    tag = TogglTag(
        id=1,
        name=faker.name(),
        workspace=workspace.id,
    )
    return {
        "workspace": workspace,
        "model": ModelTest(id=1, name=faker.name()),
        "client": client,
        "project": project,
        "tracker": TogglTracker.from_kwargs(
            id=1,
            name=faker.name(),
            workspace=workspace.id,
            start="2020-01-01T00:00:00Z",
            duration=3600,
            stop="2020-01-01T01:00:00Z",
            project=project.id,
            tags=[],
        ),
        "tag": tag,
    }


@pytest.fixture
def get_test_data(get_workspace_id, faker, number):
    return [
        {
            "id": number.randint(100, sys.maxsize),
            "workspace_id": get_workspace_id,
            "description": faker.name(),
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T01:00:00Z",
            "duration": 3600,
            "tags": [faker.name(), faker.name()],
        },
        {
            "id": number.randint(100, sys.maxsize),
            "workspace_id": get_workspace_id,
            "description": faker.name(),
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T00:30:00Z",
            "duration": 1800,
            "tags": [faker.name(), faker.name()],
        },
    ]


@pytest.fixture
def project_body(faker, get_workspace_id):
    return ProjectBody(
        name=faker.name(),
        active=True,
        color=ProjectEndpoint.get_color("red"),
    )


@pytest.fixture
def create_project(
    project_object,
    project_body,
):
    return project_object.add(project_body)
