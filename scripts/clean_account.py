from __future__ import annotations

import argparse
import logging as log
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from toggl_api import (
    generate_authentication,
)
from toggl_api.config import AuthenticationError
from toggl_api.modules.meta.cache.json_cache import JSONCache

from .utils import _client_cleanup, _path_cleanup, _project_cleanup, _tag_cleanup, _tracker_cleanup

if TYPE_CHECKING:
    from httpx import BasicAuth

DEFAULT_OBJECT: frozenset[str] = frozenset({"tracker", "project", "tag", "client"})


def _target_objects() -> set[str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--objects", nargs="+", help="Which objects not to parse.")

    args = parser.parse_args().objects
    targets = set(DEFAULT_OBJECT)
    if args is None:
        return targets

    targets.difference_update(args)

    return targets


def _clean(args: set[str], auth: BasicAuth, workspace: int) -> None:
    cache_loc = Path() / "cache"
    cache = JSONCache(cache_loc)

    if "tracker" in args:
        log.info("Cleaning trackers...")
        _tracker_cleanup(cache, workspace, auth, 1)

    if "project" in args:
        log.info("Cleaning projects...")
        _project_cleanup(cache, workspace, auth, 1)

    if "tag" in args:
        log.info("Cleaning tags...")
        _tag_cleanup(cache, workspace, auth, 1)

    if "client" in args:
        log.info("Cleaning clients...")
        _client_cleanup(cache, workspace, auth, 1)

    log.info("Cleaning cache...")
    _path_cleanup(cache_loc)


def main() -> None:
    """
    1. Check Arguments on which to clean.
    2. Verify Authentication.
    3. Clean each object
    """

    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log.basicConfig(encoding="utf-8", level=log.INFO, format=fmt)
    log.info("Starting to clean toggl-account!")

    try:
        auth = generate_authentication()
    except AuthenticationError as err:
        log.critical("Failed to find authentication: %s Exiting...", err)
        sys.exit(1)

    workspace = int(os.environ.get("TOGGL_WORKSPACE_ID", 0))
    if not workspace:
        log.critical("Default toggl worspace not set at 'TOGGL_WORKSPACE_ID'.")
        sys.exit(1)

    args = _target_objects()
    while True:
        print(f"Are you sure you want to remove all {', '.join(args)} models?")  # noqa: T201
        choice = input("[y/N] > ")
        if choice.lower() == "n":
            log.info("Exiting...")
            sys.exit(1)
        elif choice.lower() == "y":
            break

    _clean(args, auth, workspace)

    log.info("Finished Cleaning toggl account!")


if __name__ == "__main__":
    main()
