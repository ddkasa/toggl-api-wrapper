import time
from datetime import timedelta
from pathlib import Path

import httpx
import pytest

from toggl_api.modules.meta import RequestMethod, TogglCachedEndpoint
from toggl_api.modules.models import TogglTracker


class EndPointTest(TogglCachedEndpoint):
    @property
    def endpoint(self) -> str:
        return super().endpoint

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker


@pytest.fixture(scope="module")
def meta_object(config_setup, get_workspace_id, get_json_cache):
    return EndPointTest(get_workspace_id, config_setup, get_json_cache)


@pytest.fixture(scope="module")
def meta_object_sqlite(config_setup, get_workspace_id, get_sqlite_cache):
    return EndPointTest(get_workspace_id, config_setup, get_sqlite_cache)


@pytest.fixture(scope="module")
def get_test_data(get_workspace_id):
    return [
        {
            "id": 1,
            "workspace_id": get_workspace_id,
            "description": "test",
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T01:00:00Z",
            "duration": 3600,
            "tags": ["tag1", "tag2"],
        },
        {
            "id": 2,
            "workspace_id": get_workspace_id,
            "description": "test2",
            "start": "2020-01-01T00:00:00Z",
            "stop": "2020-01-01T00:30:00Z",
            "duration": 1800,
            "tags": ["tag1", "tag2"],
        },
    ]


@pytest.mark.unit()
def test_headers(meta_object):
    assert {"content-type": "application/json"} == meta_object.HEADERS


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("method", "expected"),
    [
        (RequestMethod.GET, httpx.Client().get),
        (RequestMethod.POST, httpx.Client().post),
        (RequestMethod.PUT, httpx.Client().put),
        (RequestMethod.DELETE, httpx.Client().delete),
        (RequestMethod.PATCH, httpx.Client().patch),
    ],
)
def test_get_method(meta_object, method, expected):
    method = meta_object.method(method)
    assert method.__name__ == expected.__name__
    assert method.__class__ == expected.__class__


@pytest.mark.unit()
def test_model_parameter(meta_object):
    assert meta_object.model == TogglTracker


@pytest.mark.unit()
def test_endpoint(meta_object):
    assert isinstance(meta_object.endpoint, str)


@pytest.mark.unit()
def test_cache_path(meta_object):
    assert isinstance(meta_object.cache.cache_path, Path)
    assert meta_object.cache.cache_path.parent.exists()


@pytest.mark.unit()
def test_cache_functionality(meta_object, get_test_data):
    if meta_object.cache.cache_path.exists():
        meta_object.cache.cache_path.unlink()

    meta_object.cache.save_cache(get_test_data)
    assert meta_object.cache.load_cache() == get_test_data

    meta_object.cache.cache_path.unlink()


@pytest.mark.unit()
def test_process_models(meta_object, get_test_data):
    models = [meta_object.model.from_kwargs(**i) for i in get_test_data]
    assert meta_object.process_models(get_test_data) == models
    assert all(isinstance(model, meta_object.model) for model in models)


@pytest.mark.unit()
def test_process_models_sqlite(meta_object_sqlite, get_test_data):
    models = [meta_object_sqlite.model.from_kwargs(**i) for i in get_test_data]
    assert meta_object_sqlite.process_models(get_test_data) == models
    assert all(isinstance(model, meta_object_sqlite.model) for model in models)


@pytest.mark.unit()
def test_expire_after(meta_object):
    assert meta_object.cache.expire_after == timedelta(days=1)
    meta_object.cache.expire_after = timedelta(days=3600)
    assert meta_object.cache.expire_after == timedelta(days=3600)


@pytest.mark.slow()
def test_expiration(meta_object, get_test_data):
    meta_object.expire_after = timedelta(seconds=10)
    meta_object.save_cache(get_test_data)
    assert meta_object.cache.cache_path.exists()
    time.sleep(10)
    assert meta_object.load_cache() is None
