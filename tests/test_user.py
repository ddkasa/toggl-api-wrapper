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
