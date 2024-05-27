import json
import time
from datetime import timedelta
from pathlib import Path

import pytest
import sqlalchemy as db
from sqlalchemy.orm import Session

from tests.conftest import EndPointTest
from toggl_api.modules.meta import CustomDecoder, CustomEncoder, RequestMethod
from toggl_api.modules.models import TogglTag, TogglTracker, TogglWorkspace, as_dict_custom
from toggl_api.modules.models.schema import register_tables


@pytest.fixture()
def db_conn(cache_path):
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_path = cache_path / "cache.sqlite"
    engine = db.create_engine(f"sqlite:///{cache_path}")
    conn = engine.connect()
    yield engine
    conn.close()


@pytest.fixture()
def setup_schema(db_conn):
    return register_tables(db_conn)


@pytest.mark.unit()
def test_schema(setup_schema):
    tables = {"workspace", "client", "project", "tag", "tracker"}
    assert all(table in setup_schema.tables for table in tables)


@pytest.mark.unit()
def test_model_creation(setup_schema, get_workspace_id, db_conn):
    data = {
        "id": 1100,
        "workspace_id": get_workspace_id,
        "description": "test",
        "start": "2020-01-01T00:00:00Z",
        "stop": "2020-01-01T01:00:00Z",
        "duration": 3600,
        "tags": [
            TogglTag(1, "test", get_workspace_id),
        ],
        "project_id": 1,
    }
    tracker = TogglTracker.from_kwargs(**data)

    with Session(db_conn) as session:
        session.add(TogglWorkspace(get_workspace_id, "test_workspace"))
        session.add(data["tags"][0])
        session.add(tracker)
        session.commit()

    with Session(db_conn) as session:
        assert session.query(TogglTracker).count() == 1


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
def test_cache_functionality(meta_object, model_data):
    model_data.pop("model")
    model_data = [as_dict_custom(item) for item in model_data.values()]

    meta_object.cache.session.data = model_data
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

    meta_object.cache.expire_after = timedelta(seconds=5)
    meta_object.save_cache(list(model_data.values()), RequestMethod.GET)
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
