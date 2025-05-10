"""Utilities for cleaning Toggl accounts mainly for testing."""

import contextlib
import logging
import os
import time
from pathlib import Path

from httpx import BasicAuth, HTTPError

from toggl_api import ClientEndpoint, OrganizationEndpoint, ProjectEndpoint, TagEndpoint, TrackerEndpoint
from toggl_api.config import generate_authentication

log = logging.getLogger("toggl-api-wrapper.scripts")


def _path_cleanup(cache_path: Path) -> None:
    for file in cache_path.rglob("*"):
        if file.is_dir():
            _path_cleanup(cache_path)
            continue
        file.unlink()
    if cache_path.exists():
        cache_path.rmdir()


def _tracker_cleanup(wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = TrackerEndpoint(wid, config)
    for tracker in endpoint.collect(refresh=True):
        log.info("Deleting tracker: %s", tracker)
        with contextlib.suppress(HTTPError):
            endpoint.delete(tracker)
        time.sleep(delay)


def _project_cleanup(wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = ProjectEndpoint(wid, config)
    for project in endpoint.collect(refresh=True):
        log.info("Deleting tracker: %s", project)
        with contextlib.suppress(HTTPError):
            endpoint.delete(project)
        time.sleep(delay)


def _client_cleanup(wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = ClientEndpoint(wid, config)
    for client in endpoint.collect(refresh=True):
        log.info("Deleting client: %s", client)
        with contextlib.suppress(HTTPError):
            endpoint.delete(client)
        time.sleep(delay)


def _tag_cleanup(wid: int, config: BasicAuth, delay: int = 1) -> None:
    endpoint = TagEndpoint(wid, config)
    for tag in endpoint.collect(refresh=True):
        log.info("Deleting tag: %s", tag)
        with contextlib.suppress(HTTPError):
            endpoint.delete(tag)
        time.sleep(delay)


def _org_cleanup(config: BasicAuth, delay: int = 1) -> None:
    endpoint = OrganizationEndpoint(config)
    for org in endpoint.collect(refresh=True):
        if org.name == "Do-Not-Delete":
            continue
        log.info("Deleting org: %s", org)
        with contextlib.suppress(HTTPError):
            endpoint.delete(org)
        time.sleep(delay)


def cleanup() -> None:
    """Remove all entries froma Toggl account."""
    wid = int(os.getenv("TOGGL_WORKSPACE_ID", "0"))
    config = generate_authentication()

    _project_cleanup(wid, config)
    _tracker_cleanup(wid, config)
    _client_cleanup(wid, config)
    _tag_cleanup(wid, config)
    _org_cleanup(config)
