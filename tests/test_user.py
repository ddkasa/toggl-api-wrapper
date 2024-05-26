import pytest


@pytest.mark.integration()
def test_user_endpoint(user_object):
    assert isinstance(user_object.check_authentication(), bool)


@pytest.mark.integration()
def test_current_tracker(user_object, add_tracker):
    current = user_object.current_tracker()
    assert current.name == add_tracker.name
    assert current.id == add_tracker.id
    assert current.start == add_tracker.start
