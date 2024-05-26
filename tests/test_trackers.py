import time
from datetime import datetime, timedelta, timezone

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
def test_tracker_editing(tracker_model, add_tracker):
    new_description = "new_description_test"
    data = tracker_model.edit_tracker(
        tracker_id=add_tracker.id,
        description=new_description,
    )
    assert isinstance(data, TogglTracker)
    assert data.name == new_description


@pytest.mark.integration()
def test_tracker_deletion(tracker_model):
    tracker = tracker_model.add_tracker(
        description="test_tracker",
        start=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        duration=-1,
    )
    tracker_model.delete_tracker(tracker_id=tracker.id)
    assert tracker_model.get_tracker(tracker.id, refresh=True) is None


@pytest.mark.integration()
def test_tracker_stop(tracker_model, add_tracker):
    time.sleep(1)
    tracker_model.stop_tracker(tracker_id=add_tracker.id)
    assert tracker_model.get_tracker(
        tracker_id=add_tracker.id,
        refresh=True,
    ).duration > timedelta(milliseconds=10)
