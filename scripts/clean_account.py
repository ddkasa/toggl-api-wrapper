from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from toggl_api.config import AuthenticationError, generate_authentication

from .utils import _client_cleanup, _org_cleanup, _path_cleanup, _project_cleanup, _tag_cleanup, _tracker_cleanup

if TYPE_CHECKING:
    from httpx import BasicAuth

log = logging.getLogger("toggl-api-wrapper.scripts")


DEFAULT_OBJECT: frozenset[str] = frozenset({"tracker", "project", "tag", "client", "org"})


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

    if "tracker" in args:
        log.info("Cleaning trackers...")
        _tracker_cleanup(workspace, auth, 1)

    if "project" in args:
        log.info("Cleaning projects...")
        _project_cleanup(workspace, auth, 1)

    if "tag" in args:
        log.info("Cleaning tags...")
        _tag_cleanup(workspace, auth, 1)

    if "client" in args:
        log.info("Cleaning clients...")
        _client_cleanup(workspace, auth, 1)

    if "org" in args:
        log.info("Cleaning organizations...")
        _org_cleanup(auth, 1)

    log.info("Cleaning cache...")
    _path_cleanup(cache_loc)


def main() -> None:
    """
    1. Check Arguments on which to clean.
    2. Verify Authentication.
    3. Clean each object
    """

    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(encoding="utf-8", level=logging.INFO, format=fmt)
    log.info("Starting to clean toggl-account!")

    args = _target_objects()

    try:
        auth = generate_authentication()
    except AuthenticationError as err:
        log.critical("Failed to find authentication: %s Exiting...", err)
        sys.exit(1)

    workspace = int(os.environ.get("TOGGL_WORKSPACE_ID", "0"))
    if not workspace:
        log.critical("Default toggl worspace not set at 'TOGGL_WORKSPACE_ID'.")
        sys.exit(1)

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
