from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


@dataclass
class TogglClass(metaclass=ABCMeta):
    id: int
    name: str

    @classmethod
    @abstractmethod
    def from_kwargs(cls, **kwargs) -> TogglClass:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
        )


@dataclass
class TogglWorkspace(TogglClass):
    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglWorkspace:
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
        )


@dataclass
class TogglClient(TogglClass):
    workspace: TogglWorkspace

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglClient:
        return cls(
            workspace=TogglWorkspace(id=kwargs["wid"], name=""),
            id=kwargs["id"],
            name=kwargs["name"],
        )


@dataclass
class TogglProject(TogglClass):
    workspace: TogglWorkspace
    color: str
    client: Optional[TogglClient] = field(default=None)
    active: bool = field(default=True)

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglProject:
        client = kwargs.get("client_id")
        if client:
            client = TogglClient(
                id=client,
                name="",
                workspace=kwargs["workspace_id"],
            )
        return cls(
            id=kwargs["id"],
            name=kwargs["name"],
            workspace=TogglWorkspace(id=kwargs["workspace_id"], name=""),
            color=kwargs["color"],
            client=client,
            active=kwargs["active"],
        )


@dataclass
class TogglTracker(TogglClass):
    workspace: TogglWorkspace
    start: datetime
    duration: timedelta | float
    stop: Optional[datetime | str] = field(default=None)
    project: Optional[TogglProject] = field(default=None)
    tags: list[TogglTag] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.stop:
            self.duration = timedelta(seconds=self.duration)  # type: ignore[arg-type]
            self.stop = datetime.fromisoformat(self.stop)  # type: ignore[arg-type]
        else:
            now = datetime.now(tz=UTC)
            self.duration = now - self.start

    @property
    def running(self) -> bool:
        return self.stop is None

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglTracker:
        return cls(
            id=kwargs["id"],
            name=kwargs["description"],
            workspace=TogglWorkspace(id=kwargs["workspace_id"], name=""),
            start=datetime.fromisoformat(kwargs["start"]),
            duration=kwargs["duration"],
            stop=kwargs.get("stop"),
            project=kwargs.get("project_id"),
            tags=kwargs["tags"],
        )


@dataclass
class TogglTag(TogglClass):
    workspace: TogglWorkspace

    @classmethod
    def from_kwargs(cls, **kwargs) -> TogglTag:
        return cls(
            id=kwargs["id"],
            workspace=TogglWorkspace(id=kwargs["workspace_id"], name=""),
            name=kwargs["name"],
        )
