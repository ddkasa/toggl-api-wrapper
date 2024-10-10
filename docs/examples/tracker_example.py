from datetime import timedelta
from pathlib import Path

from toggl_api import (
    TrackerBody,
    TrackerEndpoint,
    generate_authentication,
)
from toggl_api.meta.cache.sqlite_cache import SqliteCache

WORKSPACE_ID = 2313123123
AUTH = generate_authentication()
cache = SqliteCache(Path("cache"), timedelta(hours=24))
endpoint = TrackerEndpoint(WORKSPACE_ID, AUTH, cache)

body = TrackerBody("My First Tracker", tags=["My First Tag"])
tracker = endpoint.add(body)
print(tracker)
