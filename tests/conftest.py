import os
from pathlib import Path

import pytest
from httpx import BasicAuth

from src.config import generate_authentication
from src.modules.client import ClientCachedEndpoint, ClientEndpoint
from src.modules.project import ProjectCachedEndpoint, ProjectEndpoint
from src.modules.tag import CachedTagEndpoint, TagEndpoint
from src.modules.tracker import TrackerCachedEndpoint, TrackerEndpoint
from src.modules.user import UserCachedEndpoint, UserEndpoint
from src.modules.workspace import CachedWorkspaceEndpoint


@pytest.fixture(scope="session")
def client_object(get_workspace_id, config_setup) -> ClientEndpoint:
    return ClientEndpoint(get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def cached_client_object(cache_path, get_workspace_id, config_setup) -> ClientCachedEndpoint:
    return ClientCachedEndpoint(cache_path, get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def tag_object(get_workspace_id, config_setup) -> TagEndpoint:
    return TagEndpoint(get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def cached_tag_object(cache_path, get_workspace_id, config_setup) -> CachedTagEndpoint:
    return CachedTagEndpoint(cache_path, get_workspace_id, config_setup)


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
def cache_tracker_model(get_workspace_id, config_setup) -> TrackerCachedEndpoint:
    return TrackerCachedEndpoint(Path("files"), get_workspace_id, config_setup)


@pytest.fixture(scope="session")
def config_setup() -> BasicAuth:
    return generate_authentication()


@pytest.fixture(scope="session")
def cache_path() -> Path:
    path = Path("cache")
    path.mkdir(exist_ok=True, parents=True)
    return path


@pytest.fixture(scope="session")
def get_workspace_id() -> int:
    return int(os.getenv("TOGGL_WORKSPACE_ID", "0"))