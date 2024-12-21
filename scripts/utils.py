import contextlib
import logging
import os
import time
from datetime import timedelta
from pathlib import Path

from httpx import BasicAuth, HTTPError

from toggl_api import ClientEndpoint, JSONCache, OrganizationEndpoint, ProjectEndpoint, TagEndpoint, TrackerEndpoint
from toggl_api.config import generate_authentication
from toggl_api.meta.cache import TogglCache

log = logging.getLogger("toggl-api-wrapper.scripts")


def _path_cleanup(cache_path: Path) -> None:
    for file in cache_path.rglob("*"):
        if file.is_dir():
            _path_cleanup(cache_path)
            continue
        file.unlink()
    cache_path.rmdir()


def _tracker_cleanup(cache: TogglCache, wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = TrackerEndpoint(wid, config, cache)
    for tracker in endpoint.collect(refresh=True):
        log.info("Deleting tracker: %s", tracker)
        with contextlib.suppress(HTTPError):
            endpoint.delete(tracker)
        time.sleep(delay)


def _project_cleanup(cache: TogglCache, wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = ProjectEndpoint(wid, config, cache)
    projects = endpoint.collect(refresh=True)
    for project in projects:
        log.info("Deleting tracker: %s", project)
        with contextlib.suppress(HTTPError):
            endpoint.delete(project)
        time.sleep(delay)


def _client_cleanup(cache: TogglCache, wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = ClientEndpoint(wid, config, cache)
    clients = endpoint.collect(refresh=True)
    for client in clients:
        log.info("Deleting client: %s", client)
        with contextlib.suppress(HTTPError):
            endpoint.delete(client)
        time.sleep(delay)


def _tag_cleanup(cache: TogglCache, wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = TagEndpoint(wid, config, cache)
    tags = endpoint.collect(refresh=True)
    for tag in tags:
        log.info("Deleting tag: %s", tag)
        with contextlib.suppress(HTTPError):
            endpoint.delete(tag)
        time.sleep(delay)


def _org_cleanup(cache: TogglCache, config: BasicAuth, delay: int = 1) -> None:
    endpoint = OrganizationEndpoint(config, cache)
    orgs = endpoint.collect(refresh=True)
    for org in orgs:
        if org.name == "Do-Not-Delete":
            continue
        log.info("Deleting org: %s", org)
        with contextlib.suppress(HTTPError):
            endpoint.delete(org)
        time.sleep(delay)


def cleanup():
    path = Path(__file__).parent / "cache"
    wid = int(os.getenv("TOGGL_WORKSPACE_ID", "0"))
    config = generate_authentication()
    cache = JSONCache(path, timedelta(days=1))

    _project_cleanup(cache, wid, config)
    _tracker_cleanup(cache, wid, config)
    _client_cleanup(cache, wid, config)
    _tag_cleanup(cache, wid, config)
    _org_cleanup(cache, config)

    _path_cleanup(path)
