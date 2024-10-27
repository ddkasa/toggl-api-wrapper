import time
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from toggl_api import TogglTracker


@pytest.mark.order("first")
@pytest.mark.unit
def test_user_endpoint_mock(user_object, httpx_mock, config_setup):
    httpx_mock.add_response(status_code=200)
    assert user_object.verify_authentication(config_setup)

    httpx_mock.add_response(status_code=403)
    assert not user_object.verify_authentication(config_setup)

    httpx_mock.add_response(status_code=400)
    with pytest.raises(httpx.HTTPStatusError):
        assert not user_object.verify_authentication(config_setup)


@pytest.mark.order("second")
@pytest.mark.integration
def test_user_endpoint(user_object, config_setup):
    assert isinstance(user_object.verify_authentication(config_setup), bool)


@pytest.mark.integration
def test_user_information(user_object, get_workspace_id):
    details = user_object.get_details()
    assert isinstance(details, dict)
    assert details["fullname"] == "dk-test"
    assert details["default_workspace_id"] == get_workspace_id


@pytest.mark.integration
def test_current_tracker(user_object, add_tracker, tracker_object):
    current = user_object.current()
    assert isinstance(current, TogglTracker)
    assert current.name == add_tracker.name
    assert current.id == add_tracker.id
    assert current.start == add_tracker.start

    tracker_object.stop(add_tracker)
    assert user_object.current() is None


@pytest.mark.integration
def test_current_tracker_cached(user_object, add_tracker, tracker_object):
    current = user_object.current(refresh=False)
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


@pytest.mark.unit
def test_tracker_get_error(user_object, httpx_mock):
    httpx_mock.add_response(status_code=460)
    with pytest.raises(httpx.HTTPStatusError):
        user_object.get(1, refresh=True)


@pytest.mark.integration
def test_tracker_collection(user_object, add_tracker):
    collection = user_object.collect(refresh=True)
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)

    time.sleep(1)

    collection = user_object.collect()
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)


@pytest.mark.integration
def test_tracker_collection_param_since(user_object, add_tracker):
    collection = user_object.collect(since=int(datetime.now(tz=timezone.utc).timestamp()), refresh=True)
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)

    time.sleep(1)

    collection = user_object.collect(since=datetime.now(tz=timezone.utc) - timedelta(1))
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collection)


@pytest.mark.integration
def test_tracker_collection_param_before(user_object, add_tracker, tracker_object):
    tracker_object.stop(add_tracker)

    ts = datetime.now(tz=timezone.utc)
    before = ts - timedelta(weeks=1)
    collect = user_object.collect(before=before.date(), refresh=False)
    assert not any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)

    collect = user_object.collect(before=ts)
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)


@pytest.mark.integration
def test_tracker_collection_date(user_object, add_tracker):
    ts = datetime.now(tz=timezone.utc)
    collect = user_object.collect(
        start_date=ts.replace(hour=(ts.hour - 1) % 24),
        end_date=ts.replace(year=ts.year + 1),
        refresh=True,
    )
    assert any(add_tracker.id == t.id and add_tracker.name == t.name for t in collect)

    collect = user_object.collect(
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
            lambda x: x.replace(month=(x.month - 1) % 12),
            "end_date must be after the start_date!",
        ),
        (
            lambda x: x.replace(year=x.year + 1),
            lambda x: x.replace(year=x.year + 2),
            "start_date must not be earlier than the current date!",
        ),
    ],
)
def test_tracker_collection_errors(user_object, start_date, end_date, match):
    now = datetime.now(tz=timezone.utc)
    with pytest.raises(ValueError, match=match):
        user_object.collect(
            start_date=start_date(now),
            end_date=end_date(now),
            refresh=True,
        )
