import time
from datetime import timedelta

import pytest

from toggl_api import TogglTag, TogglTracker, TrackerBody


@pytest.mark.unit
def test_tracker_kwargs(get_workspace_id, faker):
    data = {
        "id": 1100,
        "workspace": get_workspace_id,
        "description": faker.name(),
        "start": "2020-01-01T00:00:00Z",
        "stop": "2020-01-01T01:00:00Z",
        "duration": 3600,
        "tags": [
            TogglTag(id=1, name=faker.name()),
            TogglTag(id=2, name=faker.name()),
        ],
    }
    tracker = TogglTracker.from_kwargs(**data)
    assert tracker.name == data["description"]
    assert isinstance(tracker, TogglTracker)
    assert tracker.id == data["id"]
    assert not tracker.running()
    assert all(tag in tracker.tags for tag in data["tags"])

    data["tags"] = [
        {"name": faker.name(), "id": 1, "workspace_id": get_workspace_id},
        {"name": faker.name(), "id": 2, "workspace_id": get_workspace_id},
    ]
    assert all(TogglTag.from_kwargs(**tag) for tag in tracker.tags for tag in data["tags"])


@pytest.mark.integration
def test_tracker_creation(add_tracker):
    assert isinstance(add_tracker, TogglTracker)


@pytest.mark.unit
def test_tracker_creation_description(tracker_object):
    body = TrackerBody()
    with pytest.raises(TypeError):
        tracker_object.add(body)

    body.description = ""
    with pytest.raises(TypeError):
        tracker_object.add(body)


@pytest.mark.integration
def test_tracker_editing(tracker_object, add_tracker, faker):
    new_description = TrackerBody(description=faker.name())
    new_description.tags = [faker.name(), faker.name()]
    data = tracker_object.edit(
        tracker=add_tracker,
        body=new_description,
    )
    assert isinstance(data, TogglTracker)
    assert data.name == new_description.description
    assert all(tag.name in new_description.tags for tag in data.tags)


@pytest.mark.integration
def test_tracker_stop(tracker_object, add_tracker, user_object):
    diff = 5
    time.sleep(diff)
    trackstop = tracker_object.stop(tracker=add_tracker)
    assert trackstop.duration >= timedelta(seconds=diff)


@pytest.mark.integration
@pytest.mark.order(after="test_tracker_stop")
def test_tracker_deletion(tracker_object, user_object, add_tracker):
    tracker_object.delete(add_tracker)
    assert add_tracker != user_object.get(add_tracker.id)
    assert add_tracker != user_object.get(add_tracker.id, refresh=True)
