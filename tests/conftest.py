import os
from pathlib import Path

import pytest
from httpx import BasicAuth


@pytest.fixture(scope="session")
def config_setup() -> tuple[str, str, str]:
    email = os.getenv("TOGGL_API_TOKEN")
    password = os.getenv("TOGGL_PASSWORD", "api_token")
    if email is None:
        email = os.getenv("TOGGL_EMAIL")
        if email is None:
            msg = "Email or API Key not set."
            raise ValueError(msg)

    return BasicAuth(email, password)


@pytest.fixture(scope="session")
def cache_path() -> Path:
    path = Path("cache")
    path.mkdir(exist_ok=True, parents=True)
    return path


@pytest.fixture(scope="session")
def get_workspace_id() -> int:
    return int(os.getenv("TOGGL_WORKSPACE_ID", ""))
