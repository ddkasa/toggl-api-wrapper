from datetime import timedelta
from pathlib import Path

from toggl_api import (
    JSONCache,
    ProjectBody,
    ProjectEndpoint,
    generate_authentication,
)

workspace_id = 2313123123
auth = generate_authentication()
cache = JSONCache(Path("cache"), timedelta(hours=24))
endpoint = ProjectEndpoint(workspace_id, auth, cache)

color = ProjectEndpoint.get_color("red")
body = ProjectBody(
    workspace_id,
    "My First Project",
    client_name="My First Client",
    color=color,
)
project = endpoint.add(body)
print(project)
