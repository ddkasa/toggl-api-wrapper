import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import BasicAuth

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


class ModelTest(TogglClass):
    def from_kwargs(self, **kwargs) -> TogglClass:
        return self(
            id=kwargs["id"],
            name=kwargs["name"],
        )


@pytest.fixture(scope="session")
def cached_client_object(get_json_cache, get_workspace_id, config_setup) -> ClientEndpoint:
    return ClientEndpoint(get_workspace_id, config_setup, get_json_cache)


class EndPointTest(TogglCachedEndpoint):
    @property
    def endpoint(self) -> str:
        return super().endpoint

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker


@pytest.fixture()
def model_data(get_workspace_id):
    workspace = TogglWorkspace(get_workspace_id, "test_workspace")

    client = TogglClient(1, "test_client", workspace)
    project = TogglProject(
        1,
        "test_project",
        workspace,
        color="#000000",
        client=client,
        active=True,
    )
    tag = TogglTag(1, "test_tag", workspace)
    return {
        "workspace": workspace,
        "model": ModelTest(1, "test_model"),
        "client": client,
        "project": project,
        "tracker": TogglTracker(
            1,
            "test_tracker",
            workspace,
            start="2020-01-01T00:00:00Z",
            duration=3600,
            stop="2020-01-01T01:00:00Z",
            project=project,
            tags=[tag],
        ),
        "tag": tag,
    }


@pytest.fixture(scope="module")
def get_test_data(get_workspace_id):
    return [
        {
            "id": 1,
            "workspace_id": get_workspace_id,
            "description": "test",
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T01:00:00Z",
            "duration": 3600,
            "tags": ["tag1", "tag2"],
        },
        {
            "id": 2,
            "workspace_id": get_workspace_id,
            "description": "test2",
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T00:30:00Z",
            "duration": 1800,
            "tags": ["tag1", "tag2"],
        },
    ]


@pytest.fixture(scope="session")
def meta_object(config_setup, get_workspace_id, get_json_cache):
    return EndPointTest(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture(scope="session")
def meta_object_sqlite(config_setup, get_workspace_id, get_sqlite_cache):
    return EndPointTest(get_workspace_id, config_setup, get_sqlite_cache)


@pytest.fixture(scope="session")
def tag_object(get_workspace_id, config_setup, get_json_cache):
    endpoint = TagEndpoint(get_workspace_id, config_setup, get_json_cache)
    yield endpoint
    all_tags = endpoint.get_tags(refresh=True)
    for tag in all_tags:
        endpoint.delete_tag(tag.id)


@pytest.fixture(scope="session")
def project_object(get_workspace_id, config_setup, get_json_cache):
    endpoint = ProjectEndpoint(get_workspace_id, config_setup, get_json_cache)
    yield endpoint
    all_projects = endpoint.get_projects(refresh=True)
    for project in all_projects:
        endpoint.delete_project(project.id)


@pytest.fixture(scope="session")
def workspace_object(get_workspace_id, config_setup, get_json_cache) -> WorkspaceEndpoint:
    return WorkspaceEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture(scope="session")
def user_object(get_workspace_id, config_setup, get_json_cache) -> UserEndpoint:
    return UserEndpoint(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture(scope="session")
def tracker_object(get_workspace_id, config_setup, get_json_cache, user_object) -> TrackerEndpoint:
    endpoint = TrackerEndpoint(get_workspace_id, config_setup, get_json_cache)
    yield endpoint
    all_trackers = user_object.get_trackers(refresh=True)
    for tracker in all_trackers:
        endpoint.delete_tracker(tracker.id)


@pytest.fixture(scope="session")
def config_setup() -> BasicAuth:
    return generate_authentication()


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
def get_workspace_id() -> int:
    return int(os.getenv("TOGGL_WORKSPACE_ID", "0"))


@pytest.fixture()
def add_tracker(tracker_object):
    tracker = tracker_object.add_tracker(
        description="test_tracker",
        start=format_iso(datetime.now(tz=timezone.utc)),
        duration=-1,
    )
    yield tracker
    tracker_object.delete_tracker(tracker_id=tracker.id)


@pytest.fixture(scope="session")
def get_sqlite_cache(cache_path):
    return SqliteCache(cache_path, timedelta(days=1))


@pytest.fixture(scope="session")
def get_json_cache(cache_path):
    cache_path.mkdir(parents=True, exist_ok=True)
    return JSONCache(cache_path, timedelta(days=1))


def pytest_sessionstart(session):
    return


def pytest_sessionfinish(session, exitstatus):
    return
