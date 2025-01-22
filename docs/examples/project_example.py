from datetime import timedelta
from pathlib import Path

from toggl_api import ProjectBody, ProjectEndpoint, TogglProject
from toggl_api.config import retrieve_togglrc_workspace_id, use_togglrc
from toggl_api.meta.cache import JSONCache

WORKSPACE_ID = retrieve_togglrc_workspace_id()
AUTH = use_togglrc()
cache = JSONCache[TogglProject](Path("cache"), timedelta(hours=24))
endpoint = ProjectEndpoint(WORKSPACE_ID, AUTH, cache)

color = ProjectEndpoint.get_color("red")
body = ProjectBody(
    "My First Project",
    client_name="My First Client",
    color=color,
)
project = endpoint.add(body)
print(project)
