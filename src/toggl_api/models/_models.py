from __future__ import annotations

import enum
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from functools import partial
from typing import Any

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from toggl_api._exceptions import NamingError
from toggl_api.utility import get_workspace, parse_iso

log = logging.getLogger("toggl-api-wrapper.model")


@dataclass
class TogglClass(ABC):
    """Base class for all Toggl dataclasses.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl model.
        name: Name or description of the Toggl project.
        timestamp: Local timestamp of when the Toggl project was last modified.
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
    def from_kwargs(cls, **kwargs: Any) -> Self:
        """Convert an arbitrary amount of kwargs to a model.

        Returns:
            A newly created `TogglClass`.
        """
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            timestamp=kwargs.get("timestamp") or datetime.now(tz=timezone.utc),
        )

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __setitem__(self, item: str, value: Any) -> None:
        setattr(self, item, value)


@dataclass
class TogglOrganization(TogglClass):
    """Data structure for Toggl organizations.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl organization.
        name: Name of the Toggl organization. Max 140 characters and min 1 character.
        timestamp: Local timestamp of when the Toggl organization was last modified.
    """

    ___tablename__ = "organization"

    def __post_init__(self) -> None:
        self.validate_name(self.name)
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> Self:
        """Convert an arbitrary amount of kwargs to an organization.

        Returns:
            A new created `TogglOrganization` object.
        """
        return super().from_kwargs(**kwargs)

    @staticmethod
    def validate_name(name: str, *, max_len: int = 140) -> None:
        """Check if a organization name is valid for the API.

        Args:
            name: The name to check as a string.
            max_len: Maximum length to allow.

        Raises:
            NamingError: If the name provided is not valid.
        """
        if not name:
            msg = "The organization name need at least have one letter!"
            raise NamingError(msg)
        if max_len and len(name) > max_len:
            msg = f"Max organization name length is {max_len}!"
            raise NamingError(msg)


@dataclass
class TogglWorkspace(TogglClass):
    """Data structure for Toggl workspaces.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl workspace.
        name: Name of the workspace.
        timestamp: Local timestamp of when the Toggl workspace was last modified.
        organization: Organization id the workspace belongs to.
    """

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
    def from_kwargs(cls, **kwargs: Any) -> Self:
        """Convert an arbitrary amount of kwargs to a workspace.

        Args:
            **kwargs: Arbitary values values to convert.

        Returns:
            An initialized `TogglWorkspace` object.
        """
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            timestamp=kwargs.get("timestamp") or datetime.now(tz=timezone.utc),
            organization=kwargs.get("organization", 0),
        )

    @staticmethod
    def validate_name(name: str, *, max_len: int = 140) -> None:
        """Check if a workspace name is valid for the API.

        Args:
            name: The name to check as a string.
            max_len: Maximum length to allow.

        Raises:
            NamingError: If the name provided is not valid.
        """
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
    """Base class for all Toggl workspace objects.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl object.
        name: Name of the object.
        timestamp: Local timestamp of when the Toggl object was last modified.
        workspace: The workspace id the Toggl object belongs to.
    """

    __tablename__ = "workspace_child"

    workspace: int = field(default=0)
    """The id of the workspace that the model belongs to."""

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> Self:
        """Convert an arbitrary amount of kwargs to workspace object.

        Args:
            **kwargs: Arbitary values values to convert.

        Returns:
            An initialized `WorkspaceChild` object.
        """
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=get_workspace(kwargs),
            timestamp=kwargs.get("timestamp") or datetime.now(tz=timezone.utc),
        )


@dataclass
class TogglClient(WorkspaceChild):
    """Data structure for Toggl clients.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl client.
        name: Name of the client.
        timestamp: Local timestamp of when the Toggl client was last modified.
        workspace: The workspace id the Toggl client belongs to.
    """

    __tablename__ = "client"

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> TogglClient:
        """Convert an arbitrary amount of kwargs to a client.

        Args:
            **kwargs: Arbitary values values to convert.

        Returns:
            An initialized `TogglClient` object.
        """
        return super().from_kwargs(**kwargs)


@dataclass
class TogglProject(WorkspaceChild):
    """Data structure for Toggl projects.

    Attributes:
        Status: An enumeration with all project statuses supported by the API.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl project.
        name: Name of the project.
        timestamp: Local timestamp of when the Toggl project was last modified.
        workspace: The workspace id the project belongs to.
        color: Color of the project. Defaults to blue. Refer to this endpoint
            [attribute][toggl_api.ProjectEndpoint.BASIC_COLORS] for basic colors.
        client: ID of the client the project belongs to. Defaults to None.
        active: Whether the project is archived or not. Defaults to True.
        start_date: When the project is supposed to start. Will default to
            the original date.
        end_date: When the projects is supposed to end. None if there is no
            deadline. Optional.
    """

    class Status(enum.Enum):
        UPCOMING = enum.auto()
        ACTIVE = enum.auto()
        ENDED = enum.auto()
        ARCHIVED = enum.auto()
        DELETED = enum.auto()

    __tablename__ = "project"

    color: str = field(default="#0b83d9")
    client: int | None = field(default=None)
    active: bool = field(default=True)

    start_date: date = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).date(),
    )
    end_date: date | None = field(default=None)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.client, TogglClient):
            self.client = self.client.id

        if isinstance(self.start_date, str):
            self.start_date = parse_iso(self.start_date).date()

        if isinstance(self.end_date, str):
            self.stop_date = parse_iso(self.end_date).date()

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> TogglProject:
        """Convert an arbitrary amount of kwargs to a project.

        Args:
            **kwargs: Arbitary values values to convert.

        Returns:
            An initialized `TogglProject` object.
        """
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

    def get_status(self) -> TogglProject.Status:
        """Derive the project status from instance attributes.

        Returns:
            A status enumeration based on the project attributes.
        """
        if not self.active:
            return TogglProject.Status.ARCHIVED
        now = datetime.now(timezone.utc)
        if now < self.start_date:
            return TogglProject.Status.UPCOMING
        if self.end_date and now >= self.end_date:
            return TogglProject.Status.ENDED
        return TogglProject.Status.ACTIVE


@dataclass
class TogglTracker(WorkspaceChild):
    """Data structure for trackers.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl tracker.
        name: Description of the tracker. Refers to tracker **description**
            inside the Toggl API.
        timestamp: Local timestamp of when the Toggl tracker was last modified.
        workspace: The workspace id the tracker belongs to.
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
    duration: timedelta | None = field(default=None)
    stop: datetime | None = field(default=None)
    project: int | None = field(default=None)
    tags: list[TogglTag] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.project, TogglProject):
            self.project = self.project.id
        if isinstance(self.start, str | datetime):
            self.start = parse_iso(self.start)  # type: ignore[assignment]
        if isinstance(self.duration, float | int):
            self.duration = timedelta(seconds=self.duration)

        if isinstance(self.stop, str | datetime):
            self.stop = parse_iso(self.stop)  # type: ignore[assignment]

    def running(self) -> bool:
        """Is the tracker running.

        Returns:
            True if the tracker is running.
        """
        return self.stop is None

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> Self:
        """Convert an arbitrary amount of kwargs to a tracker.

        Args:
            **kwargs: Arbitary values values to convert.

        Returns:
            An initialized `TogglTracker` object.
        """
        start = kwargs.get("start")
        if start is None:
            start = datetime.now(tz=timezone.utc)
            log.info(
                "No start time provided. Using current time as start time: %s",
                start,
            )

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
    def get_tags(**kwargs: Any) -> list[TogglTag]:
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
            tags = tag or tags

        return tags

    @property
    def description(self) -> str:
        """Alias for the name of the tracker.

        Returns:
            Description of the tracker.
        """
        return self.name

    @property
    def running_duration(self) -> timedelta:
        """Duration that gets calculated even if the tracker is running."""
        return self.duration or (datetime.now(tz=timezone.utc) - self.start)


@dataclass
class TogglTag(WorkspaceChild):
    """Data structure for Toggl tags.

    Params:
        id: Toggl API / Database ID (Primary Key) of the Toggl tag.
        name: Name of the tag.
        timestamp: Local timestamp of when the Toggl tag was last modified.
        workspace: The workspace id the tag belongs to.
    """

    __tablename__ = "tag"

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> TogglTag:
        """Convert an arbitrary amount of kwargs to a tag.

        Args:
            **kwargs: Arbitary values values to convert.

        Returns:
            An initialized `TogglTag` object.
        """
        return super().from_kwargs(**kwargs)
