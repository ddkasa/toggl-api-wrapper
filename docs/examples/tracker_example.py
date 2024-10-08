from datetime import timedelta
from pathlib import Path

from toggl_api import (
    TrackerBody,
    TrackerEndpoint,
    generate_authentication,
)
from toggl_api.meta.cache.sqlite_cache import SqliteCache

workspace_id = 2313123123
auth = generate_authentication()
cache = SqliteCache(Path("cache"), timedelta(hours=24))
endpoint = TrackerEndpoint(workspace_id, auth, cache)

body = TrackerBody("My First Tracker", tags=["My First Tag"])
tracker = endpoint.add(body)
print(tracker)
