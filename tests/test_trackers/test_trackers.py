import sys
import time
from datetime import timedelta

import pytest
from httpx import HTTPStatusError

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
def test_tracker_creation_dates(tracker_object, faker, httpx_mock):
    body = TrackerBody(faker.name())
    httpx_mock.add_response(status_code=200)
    assert tracker_object.add(body) is None


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


@pytest.mark.unit
def test_tracker_editing_mock(tracker_object, httpx_mock, faker, number):
    new_description = TrackerBody(description=faker.name())
    new_description.tags = [faker.name(), faker.name()]
    httpx_mock.add_response(json=None, method="PUT")
    assert tracker_object.edit(tracker=number, body=new_description) is None


@pytest.mark.integration
def test_tracker_stop(tracker_object, add_tracker, user_object):
    diff = 5
    time.sleep(diff)
    trackstop = tracker_object.stop(tracker=add_tracker)
    assert trackstop.duration >= timedelta(seconds=diff)


@pytest.mark.unit
def test_tracker_stop_mock(tracker_object, httpx_mock, number):
    httpx_mock.add_response(status_code=tracker_object.TRACKER_ALREADY_STOPPED, method="PATCH")
    assert tracker_object.stop(tracker=number) is None

    httpx_mock.add_response(status_code=401, method="PATCH")
    with pytest.raises(HTTPStatusError):
        assert tracker_object.stop(tracker=number)


@pytest.mark.integration
@pytest.mark.order(after="test_tracker_stop")
def test_tracker_deletion(tracker_object, user_object, add_tracker):
    tracker_object.delete(add_tracker)
    assert add_tracker != user_object.get(add_tracker.id, refresh=True)
    assert add_tracker != user_object.get(add_tracker.id)


@pytest.mark.integration
def test_tracker_deletion_id(tracker_object, user_object, add_tracker):
    tracker_object.delete(add_tracker.id)
    assert add_tracker != user_object.get(add_tracker.id)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("error"),
    [
        pytest.param(
            499,
            marks=pytest.mark.xfail(
                HTTPStatusError,
                reason="Raising any error thats not 200 or 409.",
            ),
        ),
        404,
        200,
    ],
)
def test_tracker_deletion_mock(tracker_object, number, httpx_mock, error):
    httpx_mock.add_response(status_code=error)
    assert tracker_object.delete(number.randint(100, sys.maxsize)) is None
