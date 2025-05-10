"""Module for generating fake/mock data for testing."""

# ruff: noqa: T201

from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random
from typing import TYPE_CHECKING, NamedTuple, TypedDict, TypeVar

from toggl_api.meta._enums import RequestMethod
from toggl_api.meta.cache._json_cache import JSONCache

if sys.version_info >= (3, 11):
    from typing import Unpack
else:
    from typing_extensions import Unpack

try:
    from faker import Faker
except ImportError as err:
    msg = "This script requires Faker to be installed. Please install with `pip install faker`."
    raise SystemExit(msg) from err

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    sqlalchemy = True
except ImportError:
    sqlalchemy = False

from toggl_api import (
    ProjectEndpoint,
    TogglClient,
    TogglOrganization,
    TogglProject,
    TogglTag,
    TogglTracker,
    TogglWorkspace,
)
from toggl_api.models import TogglClass, WorkspaceChild, register_tables

if TYPE_CHECKING:
    from collections.abc import Iterable

    from faker.typing import SeedType


log = logging.getLogger("toggl-api-wrapper")


class RandomSpec(TypedDict):
    faker: Faker
    random: Random
    total: int


def _create_orgs(**kwargs: Unpack[RandomSpec]) -> list[TogglOrganization]:
    orgs: list[TogglOrganization] = []

    for _ in range(kwargs["total"]):
        org = TogglOrganization(
            id=kwargs["random"].randint(1000, sys.maxsize),
            name=kwargs["faker"].sentence(2),
        )
        orgs.append(org)

    return orgs


def _create_workspaces(
    orgs: list[TogglOrganization],
    **kwargs: Unpack[RandomSpec],
) -> list[TogglWorkspace]:
    wpspaces: list[TogglWorkspace] = []
    for org in orgs:
        wspc = TogglWorkspace(
            id=kwargs["random"].randint(1000, sys.maxsize),
            name=kwargs["faker"].sentence(2),
            organization=org.id,
        )
        wpspaces.append(wspc)

    return wpspaces


class WorkspaceSpec(RandomSpec):
    workspaces: list[TogglWorkspace]


def _create_clients(**kwargs: Unpack[WorkspaceSpec]) -> list[TogglClient]:
    clients: list[TogglClient] = []

    for _ in range(kwargs["total"]):
        client = TogglClient(
            id=kwargs["random"].randint(1000, sys.maxsize),
            name=kwargs["faker"].last_name_male(),
            workspace=kwargs["random"].choice(kwargs["workspaces"]).id,
        )
        clients.append(client)

    return clients


T = TypeVar("T", bound=WorkspaceChild)


def _choose_random_value(
    workspace: int,
    random: Random,
    choices: list[T],
    *,
    null: bool = True,
) -> T | None:
    new_choices = list(filter(lambda x: x.workspace == workspace, choices))

    if null and random.random() >= 0.75:  # noqa: PLR2004
        return None
    return random.choice(new_choices)


def _create_projects(clients: list[TogglClient], **kwargs: Unpack[WorkspaceSpec]) -> list[TogglProject]:
    projects: list[TogglProject] = []
    random, faker = kwargs["random"], kwargs["faker"]
    current = datetime.now(tz=timezone.utc).date()
    for _ in range(kwargs["total"]):
        wid = random.choice(kwargs["workspaces"]).id
        client = _choose_random_value(wid, random, choices=clients)
        start = faker.date_between(current, current + timedelta(days=5))
        end = faker.date_between(start, start + timedelta(days=15))
        project = TogglProject(
            id=random.randint(1000, sys.maxsize),
            name=faker.first_name(),
            workspace=wid,
            client=client.id if client else None,
            color=random.choice(tuple(ProjectEndpoint.BASIC_COLORS.values())),
            start_date=start,
            end_date=end,
        )
        projects.append(project)
        current = end

    return projects


def _create_tags(**kwargs: Unpack[WorkspaceSpec]) -> list[TogglTag]:
    tags: list[TogglTag] = []

    random = kwargs["random"]

    for _ in range(kwargs["total"]):
        tag = TogglTag(
            id=random.randint(1000, sys.maxsize),
            name=kwargs["faker"].word(),
            workspace=random.choice(kwargs["workspaces"]).id,
        )
        tags.append(tag)

    return tags


def _select_random_tags(
    tags: list[TogglTag],
    workspace: int,
    total: int,
    random: Random,
) -> list[TogglTag]:
    if not total:
        return []
    workspace_tags = list(filter(lambda x: x.workspace == workspace, tags))
    return random.choices(workspace_tags, k=total)


def _create_trackers(
    tags: list[TogglTag],
    projects: list[TogglProject],
    **kwargs: Unpack[WorkspaceSpec],
) -> list[TogglTracker]:
    trackers: list[TogglTracker] = []
    random, faker = kwargs["random"], kwargs["faker"]

    current = datetime.now(tz=timezone.utc)

    for _ in range(kwargs["total"]):
        wid = random.choice(kwargs["workspaces"]).id
        project = _choose_random_value(wid, random, choices=projects)

        start = faker.date_time_between(current, current + timedelta(hours=1), tzinfo=timezone.utc)
        stop = faker.date_time_between(start, start + timedelta(hours=3), tzinfo=timezone.utc)

        tracker = TogglTracker(
            id=kwargs["random"].randint(1000, sys.maxsize),
            name=faker.sentence(nb_words=random.randint(3, 8)),
            workspace=wid,
            timestamp=start,
            start=start,
            stop=stop,
            duration=stop - start,
            project=project.id if project else None,
            tags=_select_random_tags(
                tags,
                wid,
                random.randint(0, 5),
                random,
            ),
        )
        trackers.append(tracker)
        current = stop

    return trackers


Model = TypeVar("Model", bound=TogglClass)


def _sqlite_save(cache_path: Path, *generated_models: Iterable[Model]) -> None:
    engine = create_engine(f"sqlite:///{cache_path}")
    with Session(engine) as session:
        for models in generated_models:
            for model in models:
                session.add(model)
            session.commit()


class FakeEndpoint(NamedTuple):
    MODEL: type[TogglClass]


def _json_save(cache_path: Path, *generated_models: Iterable[Model]) -> None:
    cache_path.unlink(missing_ok=True)
    cache_path = cache_path.with_suffix("")

    for models in generated_models:
        model_type = FakeEndpoint(type(next(iter(models))))
        cache = JSONCache[Model](cache_path, parent=model_type)  # type: ignore[arg-type]
        # NOTE: Intentional fake endpoint for passing the model_type to the cache.
        cache.save(models, RequestMethod.GET)


def _generate_models(cache_path: Path, seed: SeedType | None = None) -> None:
    random = Random(x=seed)
    faker = Faker()
    if seed:
        faker.seed(seed=seed)

    if cache_path.suffix == ".sqlite":
        engine = create_engine(f"sqlite:///{cache_path}")
        register_tables(engine)

    orgs = _create_orgs(faker=faker, random=random, total=3)
    workspaces = _create_workspaces(orgs, faker=faker, random=random, total=3)
    clients = _create_clients(
        faker=faker,
        random=random,
        total=20,
        workspaces=workspaces,
    )
    projects = _create_projects(
        clients=clients,
        faker=faker,
        random=random,
        total=30,
        workspaces=workspaces,
    )
    tags = _create_tags(
        faker=faker,
        random=random,
        total=100,
        workspaces=workspaces,
    )
    trackers = _create_trackers(
        tags,
        projects,
        faker=faker,
        random=random,
        total=2000,
        workspaces=workspaces,
    )
    if cache_path.suffix == ".sqlite":
        _sqlite_save(cache_path, orgs, workspaces, clients, projects, tags, trackers)
    else:
        _json_save(cache_path.with_suffix(""), orgs, workspaces, clients, projects, tags, trackers)


def _create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        "generate-data",
        description="Generate fake Toggl data for testing.",
    )
    parser.add_argument(
        type=str,
        help="custom cache path",
        dest="cache_path",
    )
    parser.add_argument(
        "-s",
        "--seed",
        default=None,
        dest="seed",
        type=str,
        help="set the seed value",
    )
    parser.add_argument(
        "-t",
        "--cache-type",
        required=False,
        default=None,
        type=str,
        choices=["sqlite", "json"],
        help="cache storage type",
    )
    return parser


def main() -> None:
    """Entry point for generating models.

    Raises:
        TypeError: If the path type is missing.
        ImportError: If the user declines to overwrite an existing file.
    """
    parser = _create_parser()
    args = parser.parse_args()
    cache_type = args.cache_type

    path = Path(args.cache_path)
    if path.suffix not in {".sqlite", ".json"}:
        if cache_type is None:
            msg = "Cache type is required if the supplied path doesn't end with 'json' or 'sqlite'!"
            raise TypeError(msg)

        path = path.with_suffix(f".{cache_type}")

    if cache_type == "sqlite" and not sqlalchemy:
        msg = (
            "If generating SQLite this script requires SQLAlchemy to be installed. "
            "Please install with `pip install sqlalchemy`."
        )
        raise ImportError(msg)

    if path.exists():
        print(f"{path} exists. Are you sure you want to overwrite?")
        while True:
            confirm = input("[Y/y]Yes | [N/n] >").casefold()
            if confirm == "y":
                break
            if confirm == "n":
                sys.exit(0)

    _generate_models(path, seed=args.seed)


if __name__ == "__main__":
    main()
