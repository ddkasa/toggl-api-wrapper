# mypy: disable-error-code=override

import contextlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from faker import Faker
from httpx import BasicAuth, HTTPError

from toggl_api.config import generate_authentication
from toggl_api.modules.client import ClientEndpoint
from toggl_api.modules.meta import JSONCache, SqliteCache, TogglCachedEndpoint
from toggl_api.modules.models import TogglClass, TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace
from toggl_api.modules.project import ProjectEndpoint
from toggl_api.modules.tag import TagEndpoint
from toggl_api.modules.tracker import TrackerEndpoint
from toggl_api.modules.user import UserEndpoint
from toggl_api.modules.workspace import WorkspaceEndpoint
from toggl_api.utility import format_iso


@pytest.fixture(scope="session")
def faker():
    return Faker()


def cleanup(cache_path):
    for file in cache_path.rglob("*"):
        if file.is_dir():
            cleanup(cache_path)
            continue
        file.unlink()
    cache_path.rmdir()


@pytest.fixture(scope="session")
def cache_path():
    path = Path(__file__).resolve().parents[0] / Path("cache")
    yield path
    if path.exists():
        cleanup(path)


@pytest.fixture(scope="session")
def config_setup() -> BasicAuth:
    return generate_authentication()


@pytest.fixture(scope="session")
def get_sqlite_cache(cache_path):
    return SqliteCache(cache_path, timedelta(days=1))


@pytest.fixture(scope="session")
def get_json_cache(cache_path):
    cache_path.mkdir(parents=True, exist_ok=True)
    return JSONCache(cache_path, timedelta(days=1))


@pytest.fixture(scope="session")
def cache_list(cache_path, get_json_cache, get_sqlite_cache):
    return (get_json_cache, get_sqlite_cache)


@pytest.fixture(scope="session")
def get_workspace_id() -> int:
    return int(os.getenv("TOGGL_WORKSPACE_ID", "0"))


@pytest.fixture(scope="session")
def workspace_object(get_workspace_id, config_setup, get_json_cache):
    return WorkspaceEndpoint(get_workspace_id, config_setup, get_json_cache)


def _project_cleanup(endpoint):
    projects = endpoint.get_projects(refresh=True)
    for project in projects:
        with contextlib.suppress(HTTPError):
            endpoint.delete_project(project)


@pytest.fixture(scope="session")
def project_object(get_workspace_id, config_setup, get_json_cache):
    endpoint = ProjectEndpoint(get_workspace_id, config_setup, get_json_cache)
    _project_cleanup(endpoint)
    yield endpoint
    _project_cleanup(endpoint)


@pytest.fixture(scope="session")
def user_object(get_workspace_id, config_setup, get_json_cache) -> UserEndpoint:
    return UserEndpoint(get_workspace_id, config_setup, get_json_cache)


def _tracker_cleanup(endpoint, user_object):
    trackers = user_object.get_trackers(refresh=True)
    for tracker in trackers:
        with contextlib.suppress(HTTPError):
            endpoint.delete_tracker(tracker)


@pytest.fixture(scope="session")
def tracker_object(get_workspace_id, config_setup, get_json_cache, user_object):
    endpoint = TrackerEndpoint(get_workspace_id, config_setup, get_json_cache)
    _tracker_cleanup(endpoint, user_object)
    yield endpoint
    _tracker_cleanup(endpoint, user_object)


@pytest.fixture()
def add_tracker(tracker_object, faker):
    tracker = tracker_object.add_tracker(
        description=faker.name(),
        start=format_iso(datetime.now(tz=timezone.utc)),
        duration=-1,
    )
    yield tracker
    tracker_object.delete_tracker(tracker)


def _client_cleanup(endpoint):
    clients = endpoint.get_clients(refresh=True)

    for client in clients:
        with contextlib.suppress(HTTPError):
            endpoint.delete_client(client)


@pytest.fixture(scope="session")
def client_object(get_json_cache, get_workspace_id, config_setup):
    endpoint = ClientEndpoint(get_workspace_id, config_setup, get_json_cache)
    _client_cleanup(endpoint)
    yield endpoint
    _client_cleanup(endpoint)


def _tag_cleanup(endpoint):
    tags = endpoint.get_tags(refresh=True)
    for tag in tags:
        with contextlib.suppress(HTTPError):
            endpoint.delete_tag(tag)


@pytest.fixture(scope="session")
def tag_object(get_workspace_id, config_setup, get_json_cache):
    endpoint = TagEndpoint(get_workspace_id, config_setup, get_json_cache)
    _tag_cleanup(endpoint)
    yield endpoint
    _tag_cleanup(endpoint)


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
        return super().endpoint

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker


@pytest.fixture(scope="session")
def meta_object(config_setup, get_workspace_id, get_json_cache):
    return EndPointTest(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture(scope="session")
def meta_object_sqlite(config_setup, get_workspace_id, get_sqlite_cache):
    return EndPointTest(get_workspace_id, config_setup, get_sqlite_cache)


def pytest_sessionstart(session: pytest.Session):
    pass


def pytest_sessionfinish(session, exitstatus):
    pass


@pytest.fixture()
def model_data(get_workspace_id, faker):
    workspace = TogglWorkspace(get_workspace_id, "test_workspace")

    client = TogglClient(
        id=1,
        name="test_client",
        workspace=workspace.id,
    )
    project = TogglProject(
        id=1,
        name="test_project",
        workspace=workspace.id,
        color="000000",
        client=client.id,
        active=True,
    )
    tag = TogglTag(
        id=1,
        name="test_tag",
        workspace=workspace.id,
    )
    return {
        "workspace": workspace,
        "model": ModelTest(id=1, name="test_model"),
        "client": client,
        "project": project,
        "tracker": TogglTracker.from_kwargs(
            id=1,
            name="test_tracker",
            workspace=workspace.id,
            start="2020-01-01T00:00:00Z",
            duration=3600,
            stop="2020-01-01T01:00:00Z",
            project=project.id,
            tags=[tag],
        ),
        "tag": tag,
    }


@pytest.fixture(scope="module")
def get_test_data(get_workspace_id):
    return [
        {
            "id": 2,
            "workspace_id": get_workspace_id,
            "description": "test",
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T01:00:00Z",
            "duration": 3600,
            "tags": ["tag1", "tag2"],
        },
        {
            "id": 3,
            "workspace_id": get_workspace_id,
            "description": "test2",
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T00:30:00Z",
            "duration": 1800,
            "tags": ["tag1", "tag2"],
        },
    ]
