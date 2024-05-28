from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import TYPE_CHECKING, Any

from toggl_api.utility import get_workspace, parse_iso

if TYPE_CHECKING:
    from typing import Optional


@dataclass
class TogglClass(metaclass=ABCMeta):
    __tablename__ = "base"
    id: int
    name: str
    timestamp: Optional[datetime] = field(
        compare=False,
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

    @classmethod
    @abstractmethod
    def from_kwargs(cls, **kwargs) -> TogglClass:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            timestamp=kwargs.get("timestamp"),
        )

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __setitem__(self, item: str, value: Any) -> None:
        setattr(self, item, value)


@dataclass
class TogglWorkspace(TogglClass):
    ___tablename__ = "workspace"

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglWorkspace:
        return super().from_kwargs(**kwargs)  # type: ignore[return-value]


@dataclass
class WorkspaceChild(TogglClass):
    __tablename__ = "workspace_child"

    workspace: int = field(default=0)

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglClass:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=get_workspace(kwargs),
            timestamp=kwargs.get("timestamp"),
        )


@dataclass
class TogglClient(WorkspaceChild):
    __tablename__ = "client"

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class TogglProject(WorkspaceChild):
    __tablename__ = "project"

    color: str = field(default="0b83d9")
    client: Optional[int] = field(default=None)
    active: bool = field(default=True)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.client, TogglClient):
            self.client = self.client.id

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglProject:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=get_workspace(kwargs),
            color=kwargs["color"],
            client=kwargs.get("client_id", kwargs.get("client")),
            active=kwargs["active"],
            timestamp=kwargs.get("timestamp"),
        )


@dataclass
class TogglTracker(WorkspaceChild):
    __tablename__ = "tracker"

    start: datetime = field(
        default_factory=partial(
            datetime.now,
            tz=timezone.utc,
        ),
    )
    duration: timedelta | float = field(default_factory=timedelta)
    stop: Optional[datetime | str] = field(default=None)
    project: Optional[int] = field(default=None)
    tags: list[TogglTag] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.project, TogglProject):
            self.project = self.project.id
        if isinstance(self.tags, list):
            self.tags = [TogglTag.from_kwargs(**t) for t in self.tags if isinstance(t, dict)]
        if isinstance(self.start, str):
            self.start = parse_iso(self.start)

        if self.stop:
            self.duration = timedelta(seconds=self.duration)  # type: ignore[arg-type]
            self.stop = parse_iso(self.stop)  # type: ignore[arg-type]
        else:
            now = datetime.now(tz=timezone.utc)
            self.duration = now - self.start

    @property
    def running(self) -> bool:
        return self.stop is None

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglTracker:
        return cls(
            id=kwargs["id"],
            name=kwargs.get("description", kwargs.get("name", "")),
            workspace=get_workspace(kwargs),
            start=parse_iso(kwargs.get("start", datetime.now(tz=timezone.utc))),
            duration=kwargs.get("duration", 0),
            stop=kwargs.get("stop"),
            project=kwargs.get("project_id", kwargs.get("project")),
            tags=kwargs["tags"] if kwargs.get("tags") else [],
            timestamp=kwargs.get("timestamp"),
        )


@dataclass
class TogglTag(WorkspaceChild):
    __tablename__ = "tag"

    def __post_init__(self) -> None:
        super().__post_init__()

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglTag:
        return super().from_kwargs(**kwargs)  # type: ignore[return-value]
