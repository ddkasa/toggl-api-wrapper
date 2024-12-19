import httpx
import pytest

from toggl_api import UserEndpoint


@pytest.mark.order("first")
@pytest.mark.unit
def test_user_endpoint_mock(httpx_mock, config_setup):
    httpx_mock.add_response(status_code=200)
    assert UserEndpoint.verify_authentication(config_setup)

    httpx_mock.add_response(status_code=403)
    assert not UserEndpoint.verify_authentication(config_setup)

    httpx_mock.add_response(status_code=400)
    with pytest.raises(httpx.HTTPStatusError):
        assert not UserEndpoint.verify_authentication(config_setup)


@pytest.mark.order("second")
@pytest.mark.integration
def test_user_endpoint(config_setup):
    assert isinstance(UserEndpoint.verify_authentication(config_setup), bool)


@pytest.mark.integration
def test_user_information(user_object, get_workspace_id):
    details = user_object.get_details()
    assert isinstance(details, dict)
    assert details["fullname"] == "dk-test"
    assert details["default_workspace_id"] == get_workspace_id
