import json
import time
from datetime import timedelta
from pathlib import Path

import pytest

from tests.conftest import EndPointTest
from toggl_api.modules.meta import CustomDecoder, CustomEncoder, RequestMethod


@pytest.mark.unit()
def test_cache_path(meta_object):
    assert isinstance(meta_object.cache.cache_path, Path)
    assert meta_object.cache.cache_path.parent.exists()


@pytest.mark.unit()
def test_cache_parent(config_setup, get_sqlite_cache, get_workspace_id):
    assert get_sqlite_cache.parent is None
    endpoint = EndPointTest(get_workspace_id, config_setup, get_sqlite_cache)
    assert endpoint.cache.parent == endpoint


@pytest.mark.unit()
def test_cache_functionality_json(meta_object, model_data):
    model_data.pop("model")
    model_data = list(model_data.values())
    meta_object.cache.save_cache(model_data, RequestMethod.GET)
    assert meta_object.cache.load_cache() == model_data
    meta_object.cache.cache_path.unlink()


@pytest.mark.unit()
def test_expire_after_setter(meta_object):
    assert meta_object.cache.expire_after == timedelta(days=1)
    meta_object.cache.expire_after = timedelta(days=3600)
    assert meta_object.cache.expire_after == timedelta(days=3600)


@pytest.mark.slow()
def test_expiration_json(meta_object, model_data):
    model_data.pop("model")
    data = list(model_data.values())
    meta_object.cache.expire_after = timedelta(seconds=5)
    meta_object.save_cache(data, RequestMethod.GET)
    assert meta_object.cache.cache_path.exists()
    time.sleep(10)
    meta_object.cache.session.load(
        meta_object.cache.cache_path,
        meta_object.cache.expire_after,
    )
    assert not meta_object.load_cache()


@pytest.mark.unit()
def test_encoder_json(model_data, cache_path):
    model_data.pop("model")
    cache_file = cache_path / "encoder.json"
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(model_data, f, cls=CustomEncoder)
    with cache_file.open("r", encoding="utf-8") as f:
        assert json.load(f, cls=CustomDecoder) == model_data
