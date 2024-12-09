from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path

import pytest
from httpx import BasicAuth

from toggl_api.config import (
    AuthenticationError,
    generate_authentication,
    retrieve_togglrc_workspace_id,
    retrieve_workspace_id,
    use_togglrc,
)


@pytest.mark.unit
def test_generate_authentication(config_setup):
    assert isinstance(config_setup, BasicAuth)


@pytest.mark.integration
def test_auth_integration(user_object):
    assert user_object.check_authentication()


@pytest.mark.unit
def test_generate_authentication_error(config_setup, monkeypatch):
    monkeypatch.delenv("TOGGL_API_TOKEN")
    with pytest.raises(AuthenticationError):
        generate_authentication()


@pytest.mark.unit
def test_get_workspace_id(get_workspace_id, monkeypatch):
    assert retrieve_workspace_id() == get_workspace_id

    monkeypatch.delenv("TOGGL_WORKSPACE_ID")

    with pytest.raises(
        ValueError,
        match="Default workspace has not been set in the environment variables.",
    ):
        assert retrieve_workspace_id()

    assert retrieve_workspace_id(get_workspace_id) == get_workspace_id


@pytest.mark.unit
def test_use_togglrc(tmp_path, faker):
    path = Path.home() / ".togglrc"
    if not path.exists():
        with pytest.raises(AuthenticationError):
            use_togglrc()

        path.touch()
        with pytest.raises(AuthenticationError):
            use_togglrc()

        path.unlink(missing_ok=True)

    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)
    file_path = tmp_path / ".togglrc"
    file_path.touch()

    config = ConfigParser(interpolation=None)
    config.write(file_path)

    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)

    config.add_section("auth")
    with file_path.open("w", encoding="utf-8") as f:
        config.write(f)
    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)

    config.set("auth", "api_token", faker.name())
    with file_path.open("w", encoding="utf-8") as f:
        config.write(f)
    assert isinstance(use_togglrc(tmp_path), BasicAuth)

    config.remove_option("auth", "api_token")
    config.set("auth", "email", faker.email())
    with file_path.open("w", encoding="utf-8") as f:
        config.write(f)
    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)

    config.set("auth", "password", faker.password())
    with file_path.open("w", encoding="utf-8") as f:
        config.write(f)
    assert isinstance(use_togglrc(tmp_path), BasicAuth)


@pytest.mark.unit
def test_use_togglrc_workspace_id(tmp_path, faker, get_workspace_id):
    with pytest.raises(FileNotFoundError):
        retrieve_togglrc_workspace_id(tmp_path)

    file_path = tmp_path / ".togglrc"
    file_path.touch()

    config = ConfigParser(interpolation=None)
    config.write(file_path)

    with pytest.raises(NoSectionError):
        retrieve_togglrc_workspace_id(tmp_path)

    config.add_section("options")
    with file_path.open("w", encoding="utf-8") as f:
        config.write(f)

    with pytest.raises(NoOptionError):
        assert retrieve_togglrc_workspace_id(tmp_path)

    config.set("options", "default_wid", str(get_workspace_id))
    with file_path.open("w", encoding="utf-8") as f:
        config.write(f)

    assert retrieve_togglrc_workspace_id(tmp_path) == get_workspace_id
