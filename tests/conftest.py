import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import BasicAuth

from toggl_api.config import generate_authentication
from toggl_api.modules.client import ClientCachedEndpoint, ClientEndpoint
from toggl_api.modules.meta.cache import JSONCache, SqliteCache
from toggl_api.modules.project import ProjectCachedEndpoint, ProjectEndpoint
from toggl_api.modules.tag import TagCachedEndpoint, TagEndpoint
from toggl_api.modules.tracker import TrackerCachedEndpoint, TrackerEndpoint
from toggl_api.modules.user import UserCachedEndpoint, UserEndpoint
from toggl_api.modules.workspace import CachedWorkspaceEndpoint
from toggl_api.utility import format_iso


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


@pytest.fixture(scope="session")
def cache_path():
    path = Path("cache")
    yield path
    # if path.exists():
    #     for file in path.rglob("*"):
    #         file.unlink()
    #     path.rmdir()


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
    cache_path = cache_path / "extra"
    cache_path.mkdir(parents=True, exist_ok=True)
    yield JSONCache(cache_path, timedelta(days=1))
    cache_path.rmdir()
