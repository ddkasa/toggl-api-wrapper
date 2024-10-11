import json
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.conftest import EndPointTest
from toggl_api.meta import CustomDecoder, CustomEncoder, JSONCache, RequestMethod
from toggl_api.models.models import TogglTracker
from toggl_api.user import UserEndpoint


@pytest.mark.unit
def test_cache_path(meta_object):
    assert isinstance(meta_object.cache.cache_path, Path)
    assert meta_object.cache.cache_path.parent.exists()


@pytest.mark.unit
def test_cache_parent(config_setup, get_sqlite_cache, get_workspace_id):
    assert get_sqlite_cache.parent is None
    endpoint = EndPointTest(get_workspace_id, config_setup, get_sqlite_cache)
    assert endpoint.cache.parent == endpoint


@pytest.mark.unit
def test_cache_json_int_arg():
    cache = JSONCache(Path("cache"), 20)
    assert cache.expire_after.seconds == 20  # noqa: PLR2004


@pytest.mark.unit
def test_cache_functionality_json(meta_object, model_data):
    model_data = model_data["tracker"]
    if meta_object.cache.cache_path.exists():
        meta_object.cache.cache_path.unlink()
    meta_object.cache.save_cache(model_data, RequestMethod.GET)
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
def test_max_length(model_data, get_json_cache):
    get_json_cache.session.data = []
    assert get_json_cache.session.max_length == 10000  # noqa: PLR2004
    get_json_cache.session.max_length = 10
    assert get_json_cache.session.max_length == 10  # noqa: PLR2004

    for _ in range(get_json_cache.session.max_length + 5):
        model_data["tracker"].id + 1
        model_data["tracker"].timestamp = datetime.now(timezone.utc)
        get_json_cache.session.data.append(model_data["tracker"])

    get_json_cache.commit()

    assert len(get_json_cache.load_cache()) == 10  # noqa: PLR2004


@pytest.mark.unit
def test_query(model_data, tracker_object, faker):
    tracker_object.cache.session.max_length = 20
    tracker_object.cache.session.data = []
    tracker_object.cache.commit()
    names = [faker.name() for _ in range(12)]
    t = model_data.pop("tracker")
    t.id = 1

    for i in range(1, 13):
        t.timestamp = datetime.now(timezone.utc)
        tracker_object.cache.session.data.append(t)
        t.id += i
        t.name = names[i - 1]

    tracker_object.cache.commit()
    assert len(tracker_object.load_cache()) == 12  # noqa: PLR2004
    assert tracker_object.query(name=names[-1])[0].name == t.name


@pytest.mark.unit
def test_query_parent(tmp_path):
    cache = JSONCache(Path(tmp_path))

    with pytest.raises(ValueError, match="Cannot load cache without parent!"):
        cache.query()


@pytest.mark.unit
def test_cache_sync(  # noqa: PLR0913, PLR0917
    tmp_path,
    user_object,
    get_test_data,
    httpx_mock,
    get_workspace_id,
    config_setup,
):
    cache1 = JSONCache(Path(tmp_path))

    user_object.cache = cache1
    tracker = get_test_data[1]
    tracker["tag_ids"] = [random.randint(1000, 100_000) for _ in range(2)]
    tracker_id = tracker["id"]
    httpx_mock.add_response(
        json=tracker,
        status_code=200,
        url=user_object.BASE_ENDPOINT + user_object.endpoint + f"time_entries/{tracker_id}",
    )

    cache2 = JSONCache(Path(tmp_path))
    endpoint = UserEndpoint(get_workspace_id, config_setup, cache2)
    assert len(cache2.load_cache()) == 0

    tracker = user_object.get(tracker_id, refresh=True)
    assert isinstance(tracker, TogglTracker)
    assert endpoint.get(tracker_id) == tracker
