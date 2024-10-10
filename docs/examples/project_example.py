from datetime import timedelta
from pathlib import Path

from toggl_api import (
    JSONCache,
    ProjectBody,
    ProjectEndpoint,
    generate_authentication,
)

WORKSPACE_ID = 2313123123
AUTH = generate_authentication()
cache = JSONCache(Path("cache"), timedelta(hours=24))
endpoint = ProjectEndpoint(WORKSPACE_ID, AUTH, cache)

color = ProjectEndpoint.get_color("red")
body = ProjectBody(
    "My First Project",
    client_name="My First Client",
    color=color,
)
project = endpoint.add(body)
print(project)
