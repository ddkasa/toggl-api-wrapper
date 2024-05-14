import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def config_setup() -> tuple[str, str, str]:
    api_token = os.getenv("TOGGL_API_TOKEN", "")
    password = os.getenv("TOGGL_PASSWORD", "")
    email = os.getenv("TOGGL_EMAIL", "")
    return api_token, password, email


@pytest.fixture(scope="session")
def cache_path() -> Path:
    path = Path("tests")
    path.mkdir(exist_ok=True, parents=True)
    return path
