import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import BasicAuth

from toggl_api.config import generate_authentication
from toggl_api.modules.client import ClientCachedEndpoint, ClientEndpoint
from toggl_api.modules.meta import JSONCache, SqliteCache, TogglCachedEndpoint
from toggl_api.modules.models import TogglClass, TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace
from toggl_api.modules.project import ProjectCachedEndpoint, ProjectEndpoint
from toggl_api.modules.tag import TagCachedEndpoint, TagEndpoint
from toggl_api.modules.tracker import TrackerCachedEndpoint, TrackerEndpoint
from toggl_api.modules.user import UserCachedEndpoint, UserEndpoint
from toggl_api.modules.workspace import CachedWorkspaceEndpoint
from toggl_api.utility import format_iso


class ModelTest(TogglClass):
    def from_kwargs(self, **kwargs) -> TogglClass:
        return self(
            id=kwargs["id"],
            name=kwargs["name"],
        )


@pytest.fixture(scope="session")
def client_object(get_workspace_id, config_setup) -> ClientEndpoint:
    return ClientEndpoint(get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def cached_client_object(
    sqlite_cache,
    get_workspace_id,
    config_setup,
) -> ClientCachedEndpoint:
    return ClientCachedEndpoint(
        get_workspace_id,
        config_setup,
        sqlite_cache,
    )


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
def tag_object(get_workspace_id, config_setup) -> TagEndpoint:
    return TagEndpoint(get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def cached_tag_object(cache_path, get_workspace_id, config_setup) -> TagCachedEndpoint:
    return TagCachedEndpoint(cache_path, get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def project_object(get_workspace_id, config_setup) -> ProjectEndpoint:
    return ProjectEndpoint(get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def cached_project_object(cache_path, get_workspace_id, config_setup) -> ProjectCachedEndpoint:
    return ProjectCachedEndpoint(cache_path, get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def workspace_object(cache_path, get_workspace_id, config_setup) -> CachedWorkspaceEndpoint:
    return CachedWorkspaceEndpoint(cache_path, get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def user_object(config_setup, get_workspace_id) -> UserEndpoint:
    return UserEndpoint(get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def cached_user_object(cache_path, get_workspace_id, config_setup) -> UserCachedEndpoint:
    return UserCachedEndpoint(cache_path, get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def tracker_model(get_workspace_id, config_setup) -> TrackerEndpoint:
    return TrackerEndpoint(get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def cache_tracker_model(get_workspace_id, config_setup, cache_path) -> TrackerCachedEndpoint:
    return TrackerCachedEndpoint(cache_path, get_workspace_id, config_setup)


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
def add_tracker(tracker_model):
    tracker = tracker_model.add_tracker(
        description="test_tracker",
        start=format_iso(datetime.now(tz=timezone.utc)),
        duration=-1,
    )
    yield tracker
    tracker_model.delete_tracker(tracker_id=tracker.id)


@pytest.fixture(scope="session")
def get_sqlite_cache(cache_path):
    return SqliteCache(cache_path, timedelta(days=1))


@pytest.fixture(scope="session")
def get_json_cache(cache_path):
    cache_path.mkdir(parents=True, exist_ok=True)
    return JSONCache(cache_path, timedelta(days=1))
