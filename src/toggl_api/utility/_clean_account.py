"""Contains an entrypoint for cleaning out a Toggl account."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, get_args

from toggl_api.config import AuthenticationError, generate_authentication

from ._cleanup import _client_cleanup, _org_cleanup, _path_cleanup, _project_cleanup, _tag_cleanup, _tracker_cleanup

if TYPE_CHECKING:
    from httpx import BasicAuth

log = logging.getLogger("toggl-api-wrapper.utility")


Sections = Literal["tracker", "project", "tag", "client", "org"]

SECTIONS: Final = frozenset(get_args(Sections))


def _generate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Clean Toggl Account")
    parser.add_argument(
        "-o",
        "--objects",
        nargs="+",
        help="Which objects not to parse.",
        choices=SECTIONS,
    )
    return parser


def _target_objects(parser: argparse.ArgumentParser) -> frozenset[Sections]:
    args = parser.parse_args().objects
    targets = SECTIONS
    if args is None:
        return targets

    return targets.difference(args)


def _clean(args: frozenset[Sections], auth: BasicAuth, workspace: int) -> None:
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
    """Entrypoint for cleaning data from a Toggl account."""
    parser = _generate_parser()
    args = _target_objects(parser)

    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(encoding="utf-8", level=logging.INFO, format=fmt)
    log.info("Starting to clean toggl-account!")

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
