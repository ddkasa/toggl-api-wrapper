import httpx
import pytest

from toggl_api import TogglTracker


@pytest.mark.order("first")
@pytest.mark.tryfirst
@pytest.mark.integration
def test_user_endpoint(user_object):
    assert isinstance(user_object.check_authentication(), bool)


@pytest.mark.integration
def test_current_tracker(user_object, add_tracker, tracker_object):
    current = user_object.current()
    assert isinstance(current, TogglTracker)
    assert current.name == add_tracker.name
    assert current.id == add_tracker.id
    assert current.start == add_tracker.start

    tracker_object.stop(add_tracker)
    assert user_object.current() is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status_code"),
    [
        405,
        pytest.param(
            440,
            marks=pytest.mark.xfail(
                raises=httpx.HTTPStatusError,
                reason="Anything that is not a 200 or 405 code should raise a HTTPStatusError.",
            ),
        ),
    ],
)
def test_current_tracker_not_running(status_code, user_object, httpx_mock):
    httpx_mock.add_response(status_code=status_code)
    assert user_object.current(refresh=True) is None


@pytest.mark.integration
def test_tracker_get(user_object, add_tracker):
    t = user_object.get(add_tracker.id)
    assert isinstance(t, TogglTracker)
    assert t.name == add_tracker.name
    assert t.id == add_tracker.id
    assert t.start == add_tracker.start

    t = user_object.get(add_tracker.id, refresh=True)
    assert isinstance(t, TogglTracker)
    assert t.name == add_tracker.name
    assert t.id == add_tracker.id
    assert t.start == add_tracker.start
