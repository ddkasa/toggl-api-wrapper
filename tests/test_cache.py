import pytest
import sqlalchemy as db
from sqlalchemy.orm import Session

from toggl_api.modules.models import TogglTag, TogglTracker, TogglWorkspace
from toggl_api.modules.models.schema import register_tables


@pytest.fixture()
def db_conn(cache_path):
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_path = cache_path / "cache.sqlite"
    engine = db.create_engine(f"sqlite:///{cache_path}")
    conn = engine.connect()
    yield engine
    conn.close()
    cache_path.unlink()


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
    }
    tracker = TogglTracker.from_kwargs(**data)

    with Session(db_conn) as session:
        session.add(TogglWorkspace(get_workspace_id, "test_workspace"))
        session.add(data["tags"][0])
        session.add(tracker)
        session.commit()

    with Session(db_conn) as session:
        assert session.query(TogglTracker).count() == 1
