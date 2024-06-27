from configparser import ConfigParser

import pytest
from httpx import BasicAuth

from toggl_api.config import AuthenticationError, generate_authentication, use_togglrc


@pytest.mark.unit()
def test_generate_authentication(config_setup):
    assert isinstance(config_setup, BasicAuth)


@pytest.mark.integration()
def test_auth_integration(user_object):
    assert user_object.check_authentication()


@pytest.mark.unit()
def test_generate_authentication_error(config_setup, monkeypatch):
    monkeypatch.delenv("TOGGL_API_TOKEN")
    with pytest.raises(AuthenticationError):
        generate_authentication()


@pytest.mark.unit()
def test_use_togglrc(tmp_path, faker):
    # REFACTOR: Could change this to create config files on fly.
    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)
    file_path = tmp_path / ".togglrc"
    file_path.touch()

    config = ConfigParser()
    config.write(file_path)

    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)

    config.add_section("auth")
    with file_path.open("w") as f:
        config.write(f)
    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)

    config.set("auth", "api_token", faker.name())
    with file_path.open("w") as f:
        config.write(f)
    assert isinstance(use_togglrc(tmp_path), BasicAuth)

    config.remove_option("auth", "api_token")
    config.set("auth", "email", faker.email())
    with file_path.open("w") as f:
        config.write(f)
    with pytest.raises(AuthenticationError):
        use_togglrc(tmp_path)

    config.set("auth", "password", faker.password())
    with file_path.open("w") as f:
        config.write(f)
    assert isinstance(use_togglrc(tmp_path), BasicAuth)
