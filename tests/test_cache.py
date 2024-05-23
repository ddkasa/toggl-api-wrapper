import pytest
import sqlalchemy as db

from toggl_api.modules.models.schema import register_tables


@pytest.fixture()
def setup_schema(cache_path):
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_path = cache_path / "cache.sqlite"
    engine = db.create_engine(f"sqlite:///{cache_path}")
    with engine.connect() as conn:
        yield register_tables(conn)
    cache_path.unlink()


@pytest.mark.unit()
def test_schema(setup_schema):
    tables = {"workspace", "client", "project", "tag", "tracker"}
    assert all(table in setup_schema.tables for table in tables)
