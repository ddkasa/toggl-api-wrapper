import time
from datetime import UTC, datetime, timedelta

import pytest

from src.modules.models import TogglTracker


@pytest.mark.unit()
def test_tracker_kwargs(get_workspace_id):
    data = {
        "id": 1100,
        "workspace_id": get_workspace_id,
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
def test_tracker_creation(tracker_model):
    data = tracker_model.add_tracker(
        description="test_create",
        start=datetime.now(tz=UTC).isoformat(timespec="seconds"),
        duration=-1,
    )
    assert isinstance(data, TogglTracker)
    tracker_model.delete_tracker(tracker_id=data.id)


@pytest.mark.integration()
def atest_tracker_editing(tracker_model):
    data = tracker_model.add_tracker(
        description="test_edit",
        start=datetime.now(tz=UTC).isoformat(timespec="seconds"),
        duration=-1,
    )
    new_description = "testing_edit"
    data = tracker_model.edit_tracker(
        tracker_id=data.id,
        description=new_description,
    )
    assert isinstance(data, TogglTracker)
    assert data.name == new_description
    tracker_model.delete_tracker(tracker_id=data.id)


@pytest.mark.integration()
def test_tracker_deletion(tracker_model, cache_tracker_model):
    data = tracker_model.add_tracker(
        description="test_delete",
        start=datetime.now(tz=UTC).isoformat(timespec="seconds"),
        duration=-1,
    )
    tracker_model.delete_tracker(tracker_id=data.id)
    assert cache_tracker_model.get_tracker(tracker_id=data.id, refresh=True) is None


@pytest.mark.integration()
def test_tracker_stop(tracker_model, cache_tracker_model):
    data = tracker_model.add_tracker(
        description="test_stop",
        start=datetime.now(tz=UTC).isoformat(timespec="seconds"),
        duration=-1,
    )
    time.sleep(1)
    tracker_model.stop_tracker(tracker_id=data.id)
    assert cache_tracker_model.get_tracker(
        tracker_id=data.id,
        refresh=True,
    ).duration > timedelta(milliseconds=10)
    tracker_model.delete_tracker(tracker_id=data.id)
