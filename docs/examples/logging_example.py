import logging
import os
from pathlib import Path

from toggl_api import JSONCache, UserEndpoint, generate_authentication

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

WORKSPACE_ID = int(os.environ.get("TOGGL_WORKSPACE_ID", 0))
AUTH = generate_authentication()
cache = JSONCache(Path("cache"))
endpoint = UserEndpoint(WORKSPACE_ID, AUTH, cache)

endpoint.check_authentication()
