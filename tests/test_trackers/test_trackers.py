import sys
import time
from datetime import datetime, timedelta, timezone

import pytest
from httpx import HTTPStatusError

from toggl_api import NamingError, TogglTag, TogglTracker, TrackerBody, TrackerEndpoint


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

    body.description = ""
    with pytest.raises(NamingError):
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
def test_tracker_stop(tracker_object, add_tracker):
    diff = 5
    time.sleep(diff)
    trackstop = tracker_object.stop(tracker=add_tracker)
    assert trackstop.duration >= timedelta(seconds=diff)


@pytest.mark.unit
def test_tracker_stop_mock(tracker_object, httpx_mock, number):
    httpx_mock.add_response(status_code=tracker_object.TRACKER_ALREADY_STOPPED, method="PATCH")
    assert tracker_object.stop(tracker=number.randint(10, sys.maxsize)) is None

    httpx_mock.add_response(status_code=401, method="PATCH")
    with pytest.raises(HTTPStatusError):
        assert tracker_object.stop(tracker=number.randint(19, sys.maxsize))


@pytest.mark.integration
@pytest.mark.order(after="test_tracker_stop")
def test_tracker_deletion(tracker_object, add_tracker):
    tracker_object.delete(add_tracker)
    assert add_tracker != tracker_object.get(add_tracker.id, refresh=True)
    assert add_tracker != tracker_object.get(add_tracker.id)


@pytest.mark.integration
def test_tracker_deletion_id(tracker_object, add_tracker):
    tracker_object.delete(add_tracker.id)
    assert add_tracker != tracker_object.get(add_tracker.id)


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


@pytest.mark.integration
def test_tracker_bulk_edit(tracker_object, add_multiple_trackers, faker):
    tracker_object.retries = 0
    body = TrackerBody(
        faker.name(),
        tags=[faker.name()],
        start=datetime.now(tz=timezone.utc),
        tag_action="add",
    )
    edit = tracker_object.bulk_edit(*add_multiple_trackers, body=body)
    assert all(t.id in edit.successes for t in add_multiple_trackers)


@pytest.mark.integration
def test_current_tracker(tracker_object, add_tracker):
    current = tracker_object.current()
    assert isinstance(current, TogglTracker)
    assert current.name == add_tracker.name
    assert current.id == add_tracker.id
    assert current.start == add_tracker.start

    tracker_object.stop(add_tracker)
    assert tracker_object.current() is None


@pytest.mark.integration
def test_current_tracker_cached(tracker_object, add_tracker):
    tracker_object.current(refresh=True)
    current = tracker_object.current(refresh=False)
    assert current.id == add_tracker.id
    assert current.name == add_tracker.name


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status_code"),
    [
        405,
        pytest.param(
            440,
            marks=pytest.mark.xfail(
                raises=HTTPStatusError,
                reason="Anything that is not a 200 or 405 code should raise a HTTPStatusError.",
            ),
        ),
    ],
)
def test_current_tracker_not_running(status_code, tracker_object, httpx_mock):
    httpx_mock.add_response(status_code=status_code)
    assert tracker_object.current(refresh=True) is None


@pytest.mark.unit
def test_current_tracker_re_raise(tracker_object, httpx_mock, monkeypatch):
    httpx_mock.add_response(status_code=405)
    monkeypatch.setattr(tracker_object, "re_raise", True)
    with pytest.raises(HTTPStatusError):
        assert tracker_object.current(refresh=True) is None


@pytest.mark.integration
def test_tracker_get(tracker_object, add_tracker):
    t = tracker_object.get(add_tracker.id, refresh=True)
    assert isinstance(t, TogglTracker)
    assert t.name == add_tracker.name
    assert t.id == add_tracker.id
    assert t.start == add_tracker.start

    t = tracker_object.get(add_tracker.id)
    assert isinstance(t, TogglTracker)
    assert t.name == add_tracker.name
    assert t.id == add_tracker.id
    assert t.start == add_tracker.start


@pytest.mark.unit
def test_tracker_get_error(tracker_object, httpx_mock):
    httpx_mock.add_response(status_code=460)
    with pytest.raises(HTTPStatusError):
        tracker_object.get(1, refresh=True)


@pytest.mark.integration
def test_tracker_collection(tracker_object: TrackerEndpoint, add_tracker):
    # NOTE: Make sure tracker object is missing from cache for the refresh.
    assert tracker_object.cache is not None
    tracker_object.cache.delete(add_tracker)
    tracker_object.cache.commit()

    collection = tracker_object.collect(refresh=True)
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)

    time.sleep(1)

    collection = tracker_object.collect()
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)


@pytest.mark.integration
def test_tracker_collection_param_since(tracker_object, add_tracker):
    collection = tracker_object.collect(since=int(datetime.now(tz=timezone.utc).timestamp()), refresh=True)
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)

    time.sleep(1)

    collection = tracker_object.collect(since=datetime.now(tz=timezone.utc) - timedelta(1))
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)


@pytest.mark.integration
def test_tracker_collection_param_before(tracker_object, add_tracker):
    tracker_object.stop(add_tracker)

    ts = datetime.now(tz=timezone.utc)
    before = ts - timedelta(weeks=1)
    collect = tracker_object.collect(before=before.date(), refresh=False)
    assert not any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)

    collect = tracker_object.collect(before=ts)
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)


@pytest.mark.integration
def test_tracker_collection_date(tracker_object, add_tracker):
    ts = datetime.now(tz=timezone.utc)
    collect = tracker_object.collect(
        start_date=ts.replace(hour=(ts.hour - 1) % 24),
        end_date=ts.replace(year=ts.year + 1),
        refresh=True,
    )
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)

    collect = tracker_object.collect(
        start_date=ts.replace(hour=(ts.hour - 1) % 24),
        end_date=ts.replace(year=ts.year + 1),
    )
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("start_date", "end_date", "match"),
    [
        (
            lambda x: x,
            lambda x: x - timedelta(weeks=4),
            "end_date must be after the start_date!",
        ),
        (
            lambda x: x + timedelta(weeks=55),
            lambda x: x + timedelta(weeks=110),
            "start_date must not be earlier than the current date!",
        ),
    ],
)
def test_tracker_collection_errors(tracker_object, start_date, end_date, match):
    now = datetime.now(tz=timezone.utc)

    with pytest.raises(ValueError, match=match):
        tracker_object.collect(
            start_date=start_date(now),
            end_date=end_date(now),
            refresh=True,
        )
