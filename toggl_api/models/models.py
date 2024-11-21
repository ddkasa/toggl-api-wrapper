from __future__ import annotations

import enum
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from functools import partial
from typing import TYPE_CHECKING, Any

from toggl_api._exceptions import NamingError
from toggl_api.utility import get_workspace, parse_iso

if TYPE_CHECKING:
    from typing import Optional


log = logging.getLogger("toggl-api-wrapper.model")


@dataclass
class TogglClass(ABC):
    """Base class for all Toggl dataclasses.

    Attributes:
        id: Toggl API / Database ID (Primary Key) of the Toggl object.
        name: Name or description of the Toggl object.
        timestamp: Timestamp of when the Toggl object was last modified.
    """

    __tablename__ = "base"
    id: int
    name: str
    timestamp: datetime = field(
        compare=False,
        repr=False,
        default_factory=partial(
            datetime.now,
            tz=timezone.utc,
        ),
    )

    def __post_init__(self) -> None:
        if isinstance(self.timestamp, str):
            self.timestamp = parse_iso(self.timestamp)
        elif self.timestamp is None:
            self.timestamp = datetime.now(tz=timezone.utc)

        self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)

    @classmethod
    @abstractmethod
    def from_kwargs(cls, **kwargs) -> TogglClass:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            timestamp=kwargs.get("timestamp", datetime.now(tz=timezone.utc)),
        )

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __setitem__(self, item: str, value: Any) -> None:
        setattr(self, item, value)


@dataclass
class TogglOrganization(TogglClass):
    """Data structure for Toggl organizations."""

    ___tablename__ = "organization"

    def __post_init__(self) -> None:
        self.validate_name(self.name)
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglOrganization:
        return super().from_kwargs(**kwargs)  # type: ignore[return-value]

    @staticmethod
    def validate_name(name: str, *, max_len: int = 140) -> None:
        """Checks if a organization name is valid for the API."""
        if not name:
            msg = "The organization name need at least have one letter!"
            raise NamingError(msg)
        if max_len and len(name) > max_len:
            msg = f"Max organization name length is {max_len}!"
            raise NamingError(msg)


@dataclass
class TogglWorkspace(TogglClass):
    """Data structure for Toggl workspaces."""

    ___tablename__ = "workspace"

    organization: int = field(default=0)

    def __post_init__(self) -> None:
        super().__post_init__()
        try:
            TogglWorkspace.validate_name(self.name)
        except NamingError as err:
            if str(err) != "No spaces allowed in the workspace name!":
                raise
            log.warning(err)
            self.name = self.name.replace(" ", "-")
            log.warning("Updated to new name: %s!", self.name)

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglWorkspace:
        return super().from_kwargs(**kwargs)  # type: ignore[return-value]

    @staticmethod
    def validate_name(name: str, *, max_len: int = 140) -> None:
        """Checks if a workspace name is valid for the API."""
        if not name:
            msg = "The workspace name need at least have one character!"
            raise NamingError(msg)
        if max_len and len(name) > max_len:
            msg = f"The max workspace name length is {max_len}!"
            raise NamingError(msg)
        if " " in name:
            msg = "No spaces allowed in the workspace name!"
            raise NamingError(msg)


@dataclass
class WorkspaceChild(TogglClass):
    """Base class for all Toggl workspace objects."""

    __tablename__ = "workspace_child"

    workspace: int = field(default=0)
    """The id of the workspace that the model belongs to."""

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs) -> WorkspaceChild:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=get_workspace(kwargs),
            timestamp=kwargs.get("timestamp", datetime.now(tz=timezone.utc)),
        )


@dataclass
class TogglClient(WorkspaceChild):
    """Data structure for Toggl clients."""

    __tablename__ = "client"

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class TogglProject(WorkspaceChild):
    """Data structure for Toggl projects.

    Attributes:
        color: Color of the project. Defaults to blue. Refer to
            [ProjectEndpoint][toggl_api.ProjectEndpoint] for
            all colors.
        client: ID of the client the project belongs to. Defaults to None.
        active: Whether the project is archived or not. Defaults to True.
        start_date: When the project is supposed to start. Will default to
            the original date.
        stop_date: When the projects is supposed to end. None if there is none
            deadline.
    """

    class Status(enum.Enum):
        UPCOMING = enum.auto()
        ACTIVE = enum.auto()
        ENDED = enum.auto()
        ARCHIVED = enum.auto()
        DELETED = enum.auto()

    __tablename__ = "project"

    color: str = field(default="0b83d9")
    client: Optional[int] = field(default=None)
    active: bool = field(default=True)

    start_date: date = field(default_factory=lambda: datetime.now(tz=timezone.utc).date())
    end_date: Optional[date] = field(default=None)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.client, TogglClient):
            self.client = self.client.id

        if isinstance(self.start_date, str):
            self.start_date = parse_iso(self.start_date).date()

        if isinstance(self.end_date, str):
            self.stop_date = parse_iso(self.end_date).date()

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglProject:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=get_workspace(kwargs),
            color=kwargs["color"],
            client=kwargs.get("client_id") or kwargs.get("client"),
            active=kwargs["active"],
            timestamp=kwargs.get("timestamp") or datetime.now(tz=timezone.utc),
            start_date=kwargs.get("start_date") or datetime.now(tz=timezone.utc).date(),
            end_date=kwargs.get("end_date"),
        )


@dataclass
class TogglTracker(WorkspaceChild):
    """Data structure for trackers.

    Attributes:
        name: Description of the tracker. Refers to tracker **description**
            inside the Toggl API. Inherited.
        start: Start time of the tracker. Defaults to time created if nothing
            is passed.
        duration: Duration of the tracker
        stop: Stop time of the tracker.
        project: Id of the project the tracker is assigned to.
        tags: List of tags.

    Methods:
        running: Whether the tracker is running.
    """

    __tablename__ = "tracker"

    start: datetime = field(
        default_factory=partial(
            datetime.now,
            tz=timezone.utc,
        ),
    )
    duration: Optional[timedelta] = field(default=None)
    stop: Optional[datetime | str] = field(default=None)
    project: Optional[int] = field(default=None)
    tags: list[TogglTag] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.project, TogglProject):
            self.project = self.project.id
        if isinstance(self.start, str | datetime):
            self.start = parse_iso(self.start)  # type: ignore[assignment]
        if isinstance(self.duration, float | int):
            self.duration = timedelta(seconds=self.duration)

        if self.stop:
            self.stop = parse_iso(self.stop)  # type: ignore[assignment]
        else:
            now = datetime.now(tz=timezone.utc)
            self.duration = now - self.start

        if isinstance(self.stop, str | datetime):
            self.stop = parse_iso(self.stop)  # type: ignore[assignment]

    def running(self) -> bool:
        return self.stop is None

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglTracker:
        start = kwargs.get("start")
        if start is None:
            start = datetime.now(tz=timezone.utc)
            log.info("No start time provided. Using current time as start time: %s", start)

        return cls(
            id=kwargs["id"],
            name=kwargs.get("description", kwargs.get("name", "")),
            workspace=get_workspace(kwargs),
            start=start,
            duration=kwargs.get("duration"),
            stop=kwargs.get("stop"),
            project=kwargs.get("project_id", kwargs.get("project")),
            tags=TogglTracker.get_tags(**kwargs),
            timestamp=kwargs.get("timestamp", datetime.now(tz=timezone.utc)),
        )

    @staticmethod
    def get_tags(**kwargs: dict) -> list[TogglTag]:
        tag_id = kwargs.get("tag_ids")
        tag = kwargs.get("tags")
        tags = []
        if tag and isinstance(tag[0], dict):
            for t in tag:
                tags.append(TogglTag.from_kwargs(**t))  # noqa: PERF401
        elif tag_id and tag:
            workspace = get_workspace(kwargs)
            for i, t in zip(tag_id, tag, strict=True):
                tags.append(TogglTag(id=i, name=t, workspace=workspace))
        else:
            tags = tag or tags  # type: ignore[assignment]

        return tags


@dataclass
class TogglTag(WorkspaceChild):
    """Data structure for Toggl tags."""

    __tablename__ = "tag"

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglTag:
        return super().from_kwargs(**kwargs)  # type: ignore[return-value]
