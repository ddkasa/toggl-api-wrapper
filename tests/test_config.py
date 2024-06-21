from pathlib import Path

import pytest
from httpx import BasicAuth

from toggl_api.config import AuthenticationError, use_togglrc


@pytest.mark.unit()
def test_generate_authentication(config_setup):
    assert isinstance(config_setup, BasicAuth)


@pytest.mark.integration()
def test_auth_integration(user_object):
    assert user_object.check_authentication()


@pytest.mark.unit()
def test_use_togglrc():
    # REFACTOR: Could change this to create config files on fly.
    rc_folder = Path("files/")
    rc_folder.mkdir(parents=True, exist_ok=True)
    assert rc_folder.exists()
    with pytest.raises(AuthenticationError):
        use_togglrc(rc_folder)

    rc_folder = Path(__file__).resolve().parents[0] / Path("extra/test_rc_1")
    assert rc_folder.exists()
    assert isinstance(use_togglrc(rc_folder), BasicAuth)

    rc_folder = Path(__file__).resolve().parents[0] / Path("extra/test_rc_2")
    assert isinstance(use_togglrc(rc_folder), BasicAuth)

    rc_folder = Path(__file__).resolve().parents[0] / Path("extra/test_rc_3")
    with pytest.raises(AuthenticationError):
        use_togglrc(rc_folder)
