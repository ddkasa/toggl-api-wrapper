import time
from datetime import timedelta

import pytest

from toggl_api.modules.models import TogglTracker


@pytest.mark.unit()
def test_tracker_kwargs(get_workspace_id):
    data = {
        "id": 1100,
        "workspace": get_workspace_id,
        "description": "test",
        "start": "2020-01-01T00:00:00Z",
        "stop": "2020-01-01T01:00:00Z",
        "duration": 3600,
        "tags": ["tag1", "tag2"],
    }
    tracker = TogglTracker.from_kwargs(**data)
    assert isinstance(tracker, TogglTracker)
    assert tracker.id == data["id"]
    assert not tracker.running


@pytest.mark.integration()
def test_tracker_creation(add_tracker):
    assert isinstance(add_tracker, TogglTracker)


@pytest.mark.integration()
def test_tracker_editing(tracker_object, add_tracker):
    new_description = "new_description_test_2"
    data = tracker_object.edit_tracker(
        tracker=add_tracker,
        description=new_description,
    )
    assert isinstance(data, TogglTracker)
    assert data.name == new_description


@pytest.mark.integration()
def test_tracker_stop(tracker_object, add_tracker, user_object):
    diff = 5
    time.sleep(diff)
    trackstop = tracker_object.stop_tracker(tracker=add_tracker)
    assert trackstop.duration >= timedelta(seconds=diff)


@pytest.mark.integration()
@pytest.mark.order(after="test_tracker_stop")
def test_tracker_deletion(tracker_object, user_object, add_tracker):
    tracker_object.delete_tracker(add_tracker)
    assert add_tracker != user_object.get_tracker(add_tracker.id)
    assert add_tracker != user_object.get_tracker(add_tracker.id, refresh=True)
