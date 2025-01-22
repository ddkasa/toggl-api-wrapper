import asyncio
from datetime import datetime, timezone

from toggl_api import ProjectBody
from toggl_api.asyncio import AsyncProjectEndpoint
from toggl_api.config import generate_authentication, retrieve_workspace_id

body = ProjectBody("New Project", start_date=datetime.now(timezone.utc).date(), active=True)

proj_ep = AsyncProjectEndpoint(retrieve_workspace_id(), generate_authentication())
project = asyncio.run(proj_ep.add(body), debug=True)
print(project)
