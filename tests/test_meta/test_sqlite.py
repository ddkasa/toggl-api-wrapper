import random
import time
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as db
from sqlalchemy.orm import Session

from toggl_api.modules.meta import RequestMethod
from toggl_api.modules.models import TogglTag, TogglTracker, TogglWorkspace, register_tables


@pytest.fixture()
def db_conn(tmp_path):
    cache_path = tmp_path / "cache.sqlite"
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
def test_model_creation(setup_schema, db_conn):
    get_workspace_id = random.randint(1, 100_000)
    data = {
        "id": random.randint(50, 100_000),
        "workspace_id": get_workspace_id,
        "description": "test",
        "start": "2020-01-01T00:00:00Z",
        "stop": "2020-01-01T01:00:00Z",
        "duration": 3600,
        "tags": [
            TogglTag(
                id=random.randint(1000, 100_000),
                name="test",
                workspace=get_workspace_id,
            ),
        ],
        "project_id": random.randint(1000, 100_000),
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
def test_db_creation(meta_object_sqlite):
    assert meta_object_sqlite.cache.cache_path.exists()


@pytest.mark.unit()
def test_add_entries_sqlite(meta_object_sqlite, model_data):
    tracker = model_data["tracker"]
    meta_object_sqlite.cache.add_entries(tracker)
    assert tracker in meta_object_sqlite.cache.load_cache()


@pytest.mark.unit()
@pytest.mark.order(after="test_add_entries_sqlite")
def test_update_entries_sqlite(meta_object_sqlite, model_data):
    tracker = model_data["tracker"]
    meta_object_sqlite.cache.add_entries(tracker)
    tracker.name = "updated_test_tracker"
    meta_object_sqlite.cache.update_entries(tracker)

    assert tracker in meta_object_sqlite.cache.load_cache()


@pytest.mark.unit()
@pytest.mark.order(after="test_update_entries_sqlite")
def test_delete_entries_sqlite(meta_object_sqlite, model_data):
    cache = meta_object_sqlite.cache.load_cache()
    meta_object_sqlite.cache.delete_entries(cache)
    assert not meta_object_sqlite.cache.load_cache().all()


@pytest.mark.unit()
def test_find_sqlite(meta_object_sqlite, model_data):
    tracker = model_data["tracker"]
    tracker.id += random.randint(50, 100_000)
    meta_object_sqlite.cache.add_entries(tracker)

    assert tracker == meta_object_sqlite.cache.find_entry(tracker)


@pytest.mark.unit()
def test_query_sqlite(tracker_object_sqlite, model_data, faker):
    names = [faker.name() for _ in range(10)]
    tracker = model_data.pop("tracker")
    tracker.timestamp = datetime.now(timezone.utc)
    tracker_object_sqlite.save_cache(tracker, RequestMethod.GET)

    d = asdict(tracker)
    for i in range(1, 11):
        d["id"] += i + 1
        d["name"] = names[i - 1]
        d["timestamp"] = datetime.now(timezone.utc)
        tracker_object_sqlite.save_cache(tracker.from_kwargs(**d), RequestMethod.GET)

    tracker_object_sqlite.cache.commit()
    assert tracker_object_sqlite.load_cache().count() == 11  # noqa: PLR2004
    assert tracker_object_sqlite.query(name=tracker.name)[0] == tracker


@pytest.mark.unit()
def test_expiration_sqlite(meta_object_sqlite, model_data):
    delay = timedelta(seconds=5)
    tracker = model_data["tracker"]
    meta_object_sqlite.cache.expire_after = delay
    assert meta_object_sqlite.cache.expire_after == delay
    meta_object_sqlite.cache.add_entries(tracker)
    time.sleep(delay.total_seconds() + 2)
    tracker_data = {"id": tracker.id, "name": tracker.name}
    assert meta_object_sqlite.cache.find_entry(tracker_data) is None


@pytest.fixture()
def user_object_sqlite(user_object, get_sqlite_cache):
    user_object.cache = get_sqlite_cache
    return user_object


@pytest.mark.unit()
def test_tracker_cache(
    user_object_sqlite,
    get_test_data,
    httpx_mock,
):
    tracker = get_test_data[1]
    tracker["tag_ids"] = [random.randint(1000, 100_000) for _ in range(2)]
    tracker_id = tracker["id"]
    httpx_mock.add_response(
        json=tracker,
        status_code=200,
        url=user_object_sqlite.BASE_ENDPOINT + user_object_sqlite.endpoint + f"time_entries/{tracker_id}",
    )

    data = user_object_sqlite.get_tracker(tracker_id, refresh=True)
    assert TogglTracker.from_kwargs(**tracker) == data
