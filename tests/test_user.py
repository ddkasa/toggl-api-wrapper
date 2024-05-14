from datetime import UTC, datetime

import pytest


@pytest.mark.integration()
def test_user_endpoint(user_object):
    assert isinstance(user_object.check_authentication(), bool)


@pytest.mark.integration()
def test_current_tracker(user_object, tracker_model):
    name = "current_tracker_test"
    start = datetime.now(tz=UTC).isoformat(timespec="seconds")
    tracker = tracker_model.add_tracker(description=name, start=start, duration=-1)
    current = user_object.current_tracker()
    assert current.name == name
    assert current.id == tracker.id
    assert current.start == datetime.fromisoformat(start)


@pytest.mark.integration()
def test_current_tracker_cached(cached_user_object, tracker_model):
    name = "current_tracker_cache_test"
    start = datetime.now(tz=UTC).isoformat(timespec="seconds")
    tracker = tracker_model.add_tracker(
        description=name,
        start=start,
        duration=-1,
    )
    current = cached_user_object.current_tracker()
    assert current.name == name
    assert current.id == tracker.id
    assert current.start == datetime.fromisoformat(start)
    assert cached_user_object.cache_path.exists()
    cached_user_object.cache_path.unlink()
    tracker_model.delete_tracker(tracker_id=tracker.id)
