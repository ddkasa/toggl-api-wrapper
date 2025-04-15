import json
import random
import sys
import time
from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.conftest import EndPointTest
from toggl_api import MissingParentError, TogglTag, TogglTracker, TrackerEndpoint
from toggl_api.meta import RequestMethod
from toggl_api.meta.cache import (
    Comparison,
    CustomDecoder,
    CustomEncoder,
    JSONCache,
    JSONSession,
    TogglQuery,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "comparison"),
    [
        (0, Comparison.EQUAL),
        ("test_value", Comparison.EQUAL),
        pytest.param(
            "testvalue",
            Comparison.GREATER_THEN,
            marks=pytest.mark.xfail(
                reason="None EQUAL(s) comparison with a string.",
                raises=TypeError,
            ),
        ),
        (0, Comparison.LESS_THEN),
        (timedelta(0), Comparison.GREATER_THEN),
        (datetime.now(tz=timezone.utc), Comparison.LESS_THEN_OR_EQUAL),
        pytest.param(
            ["test_value"],
            Comparison.GREATER_THEN,
            marks=pytest.mark.xfail(
                reason="None EQUAL(s) comparison with a sequence.",
                raises=TypeError,
            ),
        ),
        (["test_value"], Comparison.EQUAL),
    ],
)
def test_cache_query(faker, value, comparison):
    assert TogglQuery(faker.name(), value, comparison)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected", "comparison"),
    [
        (
            date.today(),  # noqa: DTZ011
            datetime.combine(datetime.today(), datetime.min.time()),  # noqa: DTZ002
            Comparison.LESS_THEN,
        ),
        (
            date.today(),  # noqa: DTZ011
            datetime.combine(datetime.today(), datetime.max.time()),  # noqa: DTZ002
            Comparison.GREATER_THEN,
        ),
        (
            date.today(),  # noqa: DTZ011
            datetime.combine(datetime.today(), datetime.min.time()),  # noqa: DTZ002
            Comparison.GREATER_THEN_OR_EQUAL,
        ),
    ],
)
def test_cache_query_conversion(faker, value, expected, comparison):
    q = TogglQuery(faker.name(), value, comparison)

    assert isinstance(q.value, datetime)
    assert q.value.hour == expected.hour
    assert q.value.minute == expected.minute
    assert q.value.second == expected.second


@pytest.mark.unit
def test_cache_path(meta_object):
    assert isinstance(meta_object.cache.cache_path, Path)
    assert meta_object.cache.cache_path.parent.exists()


@pytest.mark.unit
def test_cache_parent(config_setup, get_sqlite_cache):
    assert get_sqlite_cache._parent is None  # noqa: SLF001
    endpoint = EndPointTest(config_setup, get_sqlite_cache)
    assert endpoint.cache.parent == endpoint


@pytest.mark.unit
def test_cache_json_int_arg():
    cache = JSONCache(Path("cache"), 20)
    assert cache.expire_after.seconds == 20  # noqa: PLR2004


@pytest.mark.unit
def test_cache_functionality_json(meta_object, model_data):
    model_data = model_data["tracker"]
    if meta_object.cache.cache_path.exists():  # pragma: no cover
        meta_object.cache.cache_path.unlink()
    meta_object.cache.save(model_data, RequestMethod.GET)
    assert model_data in meta_object.load_cache()
    meta_object.cache.cache_path.unlink()


@pytest.mark.unit
def test_expire_after_setter(meta_object):
    assert meta_object.cache.expire_after == timedelta(days=1)
    meta_object.cache.expire_after = timedelta(days=3600)
    assert meta_object.cache.expire_after == timedelta(days=3600)


@pytest.mark.slow
def test_expiration_json(meta_object, model_data):
    model_data.pop("model")
    data = list(model_data.values())
    meta_object.cache.expire_after = timedelta(seconds=5)
    meta_object.save_cache(data, RequestMethod.GET)
    assert meta_object.cache.cache_path.exists()
    time.sleep(10)
    meta_object.cache.session.load(meta_object.cache.cache_path)
    assert not meta_object.load_cache()


@pytest.mark.unit
def test_encoder_json(model_data, tmp_path):
    model_data.pop("model")
    cache_file = tmp_path / "encoder.json"
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(model_data, f, cls=CustomEncoder)
    with cache_file.open("r", encoding="utf-8") as f:
        assert json.load(f, cls=CustomDecoder) == model_data


@pytest.mark.unit
def test_max_length(model_data, get_json_cache, tracker_object):
    tracker_object.cache = get_json_cache
    get_json_cache.session.data = []
    assert get_json_cache.session.max_length == 10000  # noqa: PLR2004
    get_json_cache.session.max_length = 10
    assert get_json_cache.session.max_length == 10  # noqa: PLR2004

    for _ in range(get_json_cache.session.max_length + 5):
        model_data["tracker"].id + 1
        model_data["tracker"].timestamp = datetime.now(timezone.utc)
        get_json_cache.session.data.append(model_data["tracker"])

    get_json_cache.commit()

    assert len(get_json_cache.load()) == 10  # noqa: PLR2004


@pytest.mark.unit
def test_query(model_data, tracker_object, faker):
    tracker_object.cache.expire_after = None
    tracker_object.cache.session.max_length = 20
    tracker_object.cache.session.data = []
    tracker_object.cache.commit()
    names = [faker.name() for _ in range(12)]
    t = model_data.pop("tracker")
    t.id = 1

    d = asdict(t)
    for i in range(1, 13):
        d["id"] += i
        d["name"] = names[i - 1]
        d["timestamp"] = datetime.now(timezone.utc)
        tracker_object.save_cache(TogglTracker.from_kwargs(**d), RequestMethod.GET)

    tracker_object.cache.commit()
    assert len(tracker_object.load_cache()) == 12  # noqa: PLR2004
    assert tracker_object.query(TogglQuery("name", names[0]))[0].name == names[0]
    assert len(tracker_object.query(TogglQuery("name", names[:5]))) == 5  # noqa: PLR2004


@pytest.mark.unit
def test_query_distinct(model_data, tracker_object):
    t = model_data.pop("tracker")
    t.id = 1

    d = asdict(t)
    for i in range(1, 13):
        d["id"] += i
        d["timestamp"] = datetime.now(timezone.utc)
        tracker_object.save_cache(TogglTracker.from_kwargs(**d), RequestMethod.GET)

    tracker_object.cache.commit()
    assert len(tracker_object.load_cache()) == 12  # noqa: PLR2004
    assert len(tracker_object.query(TogglQuery("name", t["name"]), distinct=True)) == 1


def _create_tag_data(faker, model_data, tracker_object, number):
    names = [faker.name() for _ in range(12)]
    t = model_data.pop("tracker")
    t.id = 1

    d = asdict(t)
    tracker_object.save_cache(TogglTracker.from_kwargs(**d), RequestMethod.GET)
    tag = TogglTag(number.randint(50, sys.maxsize), faker.name())

    for i in range(1, 3):
        d["id"] += i
        d["name"] = names[i - 1]
        d["timestamp"] = datetime.now(timezone.utc)
        d["tags"] = [tag]
        tracker_object.save_cache(TogglTracker.from_kwargs(**d), RequestMethod.GET)

    return tag


@pytest.mark.unit
def test_query_tag(model_data, tracker_object, faker, number):
    tag = _create_tag_data(faker, model_data, tracker_object, number)

    tracker_object.cache.commit()
    assert len(tracker_object.load_cache()) == 3  # noqa: PLR2004
    assert len(tracker_object.query(TogglQuery("tags", [tag]))) == 2  # noqa: PLR2004


@pytest.mark.unit
def test_query_tag_distict(model_data, tracker_object, faker, number):
    tag = _create_tag_data(faker, model_data, tracker_object, number)

    tracker_object.cache.commit()
    assert len(tracker_object.load_cache()) == 3  # noqa: PLR2004
    assert len(tracker_object.query(TogglQuery("tags", [tag]), distinct=True)) == 2  # noqa: PLR2004


@pytest.mark.unit
def test_query_parent(tmp_path):
    cache = JSONCache(Path(tmp_path))

    with pytest.raises(MissingParentError):
        cache.query()


# FIX:: Flaky test that will fail occasionally on windows testing.
# NOTE: Suspicion that time accuracy is the causing issues.
@pytest.mark.unit
@pytest.mark.flaky(rerun_except="AssertionError", reruns=3)
def test_cache_sync(
    tmpdir,
    get_test_data,
    httpx_mock,
    get_workspace_id,
    config_setup,
):
    path = Path(tmpdir)
    cache2 = JSONCache(path)
    endpoint = TrackerEndpoint(get_workspace_id, config_setup, cache2)
    assert len(cache2.load()) == 0

    cache1 = JSONCache(path)
    tracker_object = TrackerEndpoint(get_workspace_id, config_setup, cache1)
    assert len(tracker_object.cache.load()) == 0

    tracker = get_test_data[1]
    tracker["tag_ids"] = [random.randint(1000, 100_000) for _ in range(2)]
    tracker_id = tracker["id"]
    httpx_mock.add_response(json=tracker)
    tracker = tracker_object.get(tracker_id, refresh=True)
    assert isinstance(tracker, TogglTracker)

    if sys.platform == "win32":  # pragma: no cover # NOTE: Windows Only
        time.sleep(0.1)

    assert endpoint.get(tracker_id) == tracker


@pytest.mark.unit
@pytest.mark.parametrize(
    "comparison",
    [
        pytest.param(
            None,
            marks=pytest.mark.xfail(
                reason="Not a comparison enumeration.",
                raises=NotImplementedError,
            ),
        ),
        Comparison.LESS_THEN,
        Comparison.GREATER_THEN,
        Comparison.GREATER_THEN_OR_EQUAL,
        Comparison.LESS_THEN_OR_EQUAL,
        Comparison.EQUAL,
    ],
)
def test_match_query_helper(tracker_object, comparison, faker, number):
    cache = tracker_object.cache
    params = TogglQuery("start", datetime.now(tz=timezone.utc), comparison)

    model = TogglTracker(number, faker.name())

    assert isinstance(cache._match_query(model, params), bool)  # noqa: SLF001


@pytest.mark.unit
def test_json_session_refresh(model_data, tmpdir):
    tracker = model_data["tracker"]

    path = Path(tmpdir) / "model.json"

    trackers = []
    for i in range(50, 100):
        tracker = deepcopy(tracker)
        tracker["id"] = i
        tracker["timestamp"] = datetime.now(tz=timezone.utc)
        trackers.append(tracker)
    session = JSONSession()
    session.load(path)
    session.commit(path)
    assert not session.refresh(path)
    session.data = trackers

    new_trackers = []
    for i in range(75, 150):
        tracker = deepcopy(tracker)
        tracker["id"] = i
        tracker["timestamp"] = datetime.now(tz=timezone.utc)
        new_trackers.append(tracker)
    new_session = JSONSession()
    new_session.load(path)
    new_session.data = new_trackers

    assert not new_session.refresh(path)
    assert not session.refresh(path)

    new_session.commit(path)

    tracker = deepcopy(tracker)
    tracker["id"] = 149
    tracker["timestamp"] = datetime.now(tz=timezone.utc) + timedelta(days=1)
    session.data.append(tracker)

    tracker = deepcopy(tracker)
    tracker["id"] = 170
    tracker["timestamp"] = datetime.now(tz=timezone.utc) + timedelta(days=1)
    session.data.append(tracker)

    assert session.refresh(path)
    assert len(session.data) == 76  # noqa: PLR2004
