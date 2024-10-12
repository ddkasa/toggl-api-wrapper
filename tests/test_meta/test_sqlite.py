import random
import time
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy.orm import Query, Session

from toggl_api.meta import RequestMethod
from toggl_api.meta.cache.base_cache import Comparison, TogglQuery
from toggl_api.meta.cache.sqlite_cache import SqliteCache
from toggl_api.models import TogglTag, TogglTracker, TogglWorkspace
from toggl_api.models._decorators import UTCDateTime  # noqa: PLC2701
from toggl_api.models.schema import register_tables


@pytest.fixture
def db_conn(tmp_path):
    cache_path = tmp_path / "cache.sqlite"
    engine = sqlalchemy.create_engine(f"sqlite:///{cache_path}")
    conn = engine.connect()
    yield engine
    conn.close()


@pytest.fixture
def setup_schema(db_conn):
    return register_tables(db_conn)


@pytest.mark.unit
def test_cache_int_arg():
    cache = SqliteCache(Path("cache"), 20)
    assert cache.expire_after.seconds == 20  # noqa: PLR2004


@pytest.mark.unit
@pytest.mark.parametrize(
    "table",
    [
        "workspace",
        "client",
        "project",
        "tag",
        "tracker",
    ],
)
def test_schema(table, setup_schema):
    assert table in setup_schema.tables


@pytest.mark.unit
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


@pytest.mark.unit
def test_db_creation(meta_object_sqlite):
    assert meta_object_sqlite.cache.cache_path.exists()


@pytest.mark.unit
def test_add_entries_sqlite(meta_object_sqlite, model_data):
    tracker = model_data["tracker"]
    meta_object_sqlite.cache.add_entries(tracker)
    assert tracker in meta_object_sqlite.cache.load_cache()


@pytest.mark.unit
def test_add_entries_sqlite_parent(meta_object_sqlite, model_data):
    tracker = model_data["tracker"]
    meta_object_sqlite.cache.add_entries(tracker)
    meta_object_sqlite.cache.parent = None
    with pytest.raises(ValueError, match="Cannot load cache without parent set!"):
        assert tracker in meta_object_sqlite.cache.load_cache()


@pytest.mark.unit
@pytest.mark.order(after="test_add_entries_sqlite")
def test_update_entries_sqlite(meta_object_sqlite, model_data):
    tracker = model_data["tracker"]
    meta_object_sqlite.cache.add_entries(tracker)
    tracker.name = "updated_test_tracker"
    meta_object_sqlite.cache.update_entries(tracker)

    assert tracker in meta_object_sqlite.cache.load_cache()


@pytest.mark.unit
@pytest.mark.order(after="test_update_entries_sqlite")
def test_delete_entries_sqlite(meta_object_sqlite, model_data):
    cache = meta_object_sqlite.cache.load_cache()
    meta_object_sqlite.cache.delete_entries(cache)
    assert not meta_object_sqlite.cache.load_cache().all()


@pytest.mark.unit
def test_find_sqlite(meta_object_sqlite, model_data):
    tracker = model_data["tracker"]
    tracker.id += random.randint(50, 100_000)
    meta_object_sqlite.cache.add_entries(tracker)
    assert tracker == meta_object_sqlite.cache.find_entry(tracker)


@pytest.mark.unit
def test_find_sqlite_parent(meta_object_sqlite):
    meta_object_sqlite.cache.parent = None
    with pytest.raises(ValueError, match="Cannot load cache without parent set!"):
        meta_object_sqlite.cache.find_entry({"id": 5})


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
def test_match_query_helper(tracker_object_sqlite, comparison, tmp_path, number):
    cache = tracker_object_sqlite.cache
    params = TogglQuery("name", number, comparison)
    query = cache.query(params)

    assert isinstance(cache._match_query(params, query), Query)  # noqa: SLF001


@pytest.mark.unit
def test_query_sqlite(tracker_object_sqlite, model_data, faker):
    names = {faker.name() for _ in range(10)}
    tracker = model_data.pop("tracker")
    tracker.timestamp = datetime.now(timezone.utc)
    tracker_object_sqlite.save_cache(tracker, RequestMethod.GET)

    d = asdict(tracker)
    total_picks = 5
    picked_names = set()
    for i, name in enumerate(names):
        if i < total_picks:
            picked_names.add(name)

        d["id"] += i + 1
        d["name"] = name
        d["timestamp"] = datetime.now(timezone.utc)
        tracker_object_sqlite.save_cache(tracker.from_kwargs(**d), RequestMethod.GET)

    tracker_object_sqlite.cache.commit()
    assert tracker_object_sqlite.load_cache().count() == 11  # noqa: PLR2004
    assert tracker_object_sqlite.query(TogglQuery("name", tracker.name))[0] == tracker
    assert tracker_object_sqlite.query(TogglQuery("name", list(picked_names))).count() == total_picks


@pytest.mark.unit
def test_query_sqlite_distinct(tracker_object_sqlite, model_data, faker):
    name = faker.name()
    tracker = model_data.pop("tracker")
    tracker.timestamp = datetime.now(timezone.utc)
    tracker_object_sqlite.save_cache(tracker, RequestMethod.GET)

    d = asdict(tracker)
    for i in range(2):
        d["id"] += i
        d["name"] = name
        d["timestamp"] = datetime.now(timezone.utc)
        tracker_object_sqlite.save_cache(tracker.from_kwargs(**d), RequestMethod.GET)

    assert tracker_object_sqlite.query(TogglQuery("name", name), distinct=True).count() == 1


@pytest.mark.unit
def test_query_sqlite_parent(meta_object_sqlite):
    meta_object_sqlite.cache.parent = None
    with pytest.raises(ValueError, match="Cannot load cache without parent set!"):
        meta_object_sqlite.cache.find_entry({"id": 5})


@pytest.mark.unit
def test_expiration_sqlite(meta_object_sqlite, model_data):
    delay = timedelta(seconds=5)
    tracker = model_data["tracker"]
    meta_object_sqlite.cache.expire_after = delay
    assert meta_object_sqlite.cache.expire_after == delay
    meta_object_sqlite.cache.add_entries(tracker)
    time.sleep(delay.total_seconds() + 2)
    tracker_data = {"id": tracker.id, "name": tracker.name}
    assert meta_object_sqlite.cache.find_entry(tracker_data) is None


@pytest.fixture
def user_object_sqlite(user_object, get_sqlite_cache):
    user_object.cache = get_sqlite_cache
    return user_object


@pytest.mark.unit
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

    data = user_object_sqlite.get(tracker_id, refresh=True)
    assert TogglTracker.from_kwargs(**tracker) == data


@pytest.mark.unit
def test_sqlite_save(tmp_path, get_workspace_id):
    cache = SqliteCache(Path(tmp_path))
    assert cache.save_cache(TogglTag(0, "awdad", None, get_workspace_id), object()) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value"),
    [
        pytest.param(
            datetime.now(),  # noqa: DTZ005
            marks=pytest.mark.xfail(
                reason="Every datetime should have a timezone.",
                raises=ValueError,
            ),
        ),
        pytest.param(
            date.today(),  # noqa: DTZ011
            marks=pytest.mark.xfail(
                reason="Only datetime objects accepted.",
                raises=TypeError,
            ),
        ),
        None,
    ],
)
def test_utc_datetime_decorator_error(value):
    decorator = UTCDateTime()
    assert decorator.process_bind_param(value, None) is None
