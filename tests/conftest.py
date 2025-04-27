# mypy: disable-error-code=override

import os
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import BasicAuth

from toggl_api import (
    ClientBody,
    ClientEndpoint,
    ProjectBody,
    ProjectEndpoint,
    TagEndpoint,
    TogglOrganization,
    TrackerBody,
    TrackerEndpoint,
    UserEndpoint,
    WorkspaceEndpoint,
)
from toggl_api.config import generate_authentication
from toggl_api.meta import TogglCachedEndpoint
from toggl_api.meta.cache import JSONCache, SqliteCache
from toggl_api.models import TogglClass, TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace
from toggl_api.reports import ReportBody
from toggl_api.utility._cleanup import cleanup  # noqa: PLC2701


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


@pytest.fixture(scope="session")
def organization_id() -> int:
    return int(os.getenv("TOGGL_ORGANIZATION_ID", "0"))


@pytest.fixture(scope="session")
def user_id() -> int:
    return int(os.getenv("TOGGL_USER_ID", "0"))


@pytest.fixture
def workspace_object(organization_id, config_setup, get_json_cache):
    return WorkspaceEndpoint(organization_id, config_setup, get_json_cache)


@pytest.fixture
def project_object(get_workspace_id, config_setup, get_json_cache):
    return ProjectEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture
def user_object(config_setup, get_json_cache) -> UserEndpoint:
    return UserEndpoint(config_setup)


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
        return cls(  # pragma: no cover
            id=kwargs["id"],
            name=kwargs["name"],
        )


class EndPointTest(TogglCachedEndpoint):
    MODEL = TogglTracker


@pytest.fixture
def meta_object(config_setup, get_workspace_id, get_json_cache):
    return EndPointTest(config_setup, get_json_cache)


@pytest.fixture
def meta_object_sqlite(config_setup, get_workspace_id, get_sqlite_cache):
    return EndPointTest(config_setup, get_sqlite_cache)


def pytest_sessionstart(session: pytest.Session):  # pragma: no cover
    marks = session.config.getoption("-m", default="")
    if not marks or "integration" in marks:
        cleanup()


def pytest_sessionfinish(session, exitstatus):  # pragma: no cover
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
def gen_proj_bd(faker, get_workspace_id):
    def gen_proj_bd():
        return ProjectBody(
            name=faker.name(),
            active=True,
            color=ProjectEndpoint.get_color("red"),
        )

    return gen_proj_bd


@pytest.fixture
def gen_proj(
    project_object,
    gen_proj_bd,
):
    return project_object.add(gen_proj_bd())


@pytest.fixture
def gen_project(faker, number):
    def gen_proj():
        return TogglProject(number.randint(100, sys.maxsize), faker.name())

    return gen_proj


@pytest.fixture
def add_multiple_trackers(tracker_object, faker, gen_proj):
    trackers = []
    for i in range(5, 10):
        time.sleep(1)
        body = TrackerBody(
            description=faker.name(),
            project_id=gen_proj.id,
            start=datetime.now(tz=timezone.utc).replace(hour=i),
            stop=datetime.now(tz=timezone.utc).replace(hour=i + 1),
        )
        trackers.append(tracker_object.add(body=body))

    yield trackers
    for tracker in trackers:
        time.sleep(1)
        tracker_object.delete(tracker)


@pytest.fixture
def generate_tracker(faker, number, get_workspace_id):
    def gen_tracker():
        return TogglTracker(
            number.randint(50, sys.maxsize),
            faker.name(),
            workspace=get_workspace_id,
            start=datetime.now(tz=timezone.utc),
        )

    return gen_tracker


@pytest.fixture
def gen_tracker_bd(faker, number, get_workspace_id):
    def gen_tracker():
        return TrackerBody(
            faker.name(),
            start=datetime.now(tz=timezone.utc),
        )

    return gen_tracker


@pytest.fixture
def gen_client(faker, number, get_workspace_id):
    def gen_client():
        return TogglClient(
            number.randint(50, sys.maxsize),
            faker.name(),
            workspace=get_workspace_id,
        )

    return gen_client


@pytest.fixture
def gen_tag(faker, number, get_workspace_id):
    def gen_tag():
        return TogglTag(
            number.randint(50, sys.maxsize),
            faker.name(),
            workspace=get_workspace_id,
        )

    return gen_tag


@pytest.fixture
def gen_workspace(faker, number, organization_id):
    def gen_workspace():
        return TogglWorkspace(
            number.randint(50, sys.maxsize),
            faker.name(),
            organization=organization_id,
        )

    return gen_workspace


@pytest.fixture
def gen_org(faker, number):
    def gen_org():
        return TogglOrganization(
            number.randint(50, sys.maxsize),
            faker.name(),
        )

    return gen_org


@pytest.fixture
def report_body(get_workspace_id):
    return ReportBody(date.today(), date.today())  # noqa: DTZ011


@pytest.fixture
def create_client_body(get_workspace_id, faker):
    return ClientBody(name=faker.name())


@pytest.fixture
def create_client(client_object, create_client_body):
    return client_object.add(create_client_body)
