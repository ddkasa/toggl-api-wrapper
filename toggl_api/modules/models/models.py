from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from toggl_api.utility import get_workspace, parse_iso

if TYPE_CHECKING:
    from collections.abc import Hashable
    from typing import Optional


@dataclass
class TogglClass(metaclass=ABCMeta):
    __tablename__ = "base"
    id: int
    name: str

    @classmethod
    @abstractmethod
    def from_kwargs(cls, **kwargs) -> TogglClass:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
        )

    def __getitem__(self, item: Hashable) -> Any:
        return getattr(self, item)

    def __setitem__(self, item: Hashable, value: Any) -> None:
        setattr(self, item, value)


@dataclass
class TogglWorkspace(TogglClass):
    ___tablename__ = "workspace"

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglWorkspace:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
        )


@dataclass
class WorkspaceChild(TogglClass):
    __tablename__ = "workspace_child"

    workspace: int

    def __post_init__(self) -> None:
        if isinstance(self.workspace, TogglWorkspace):
            self.workspace = self.workspace.id

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglClass:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=get_workspace(kwargs),
        )


@dataclass
class TogglClient(WorkspaceChild):
    __tablename__ = "client"

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class TogglProject(WorkspaceChild):
    __tablename__ = "project"

    color: str
    client: Optional[int] = field(default=None)
    active: bool = field(default=True)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.client, TogglClient):
            self.client = self.client.id

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglProject:
        client = kwargs.get("client_id", kwargs.get("client"))
        workspace = get_workspace(kwargs)
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=workspace,
            color=kwargs["color"],
            client=client,
            active=kwargs["active"],
        )


@dataclass
class TogglTracker(WorkspaceChild):
    __tablename__ = "tracker"

    start: datetime
    duration: timedelta | float
    stop: Optional[datetime | str] = field(default=None)
    project: Optional[int] = field(default=None)
    tags: list[TogglTag] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.project, TogglProject):
            self.project = self.project.id
        if isinstance(self.tags, list):
            self.tags = [TogglTag.from_kwargs(**t) for t in self.tags if isinstance(t, dict)]

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
        workspace = get_workspace(kwargs)

        return cls(
            id=kwargs["id"],
            name=kwargs.get("description", kwargs.get("name", "")),
            workspace=workspace,
            start=parse_iso(kwargs["start"]),
            duration=kwargs["duration"],
            stop=kwargs.get("stop"),
            project=kwargs.get("project_id"),
            tags=kwargs["tags"],
        )


@dataclass
class TogglTag(WorkspaceChild):
    __tablename__ = "tag"

    def __post_init__(self) -> None:
        super().__post_init__()
