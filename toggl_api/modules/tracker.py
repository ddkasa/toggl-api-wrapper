from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Final, Literal, Optional

from httpx import HTTPStatusError

from toggl_api.modules.meta import RequestMethod, TogglCachedEndpoint
from toggl_api.modules.models import TogglTracker
from toggl_api.utility import format_iso


@dataclass
class TrackerBody:
    workspace_id: Optional[int] = field(default=None)
    description: Optional[str] = field(default=None)
    duration: Optional[int | timedelta] = field(default=None)
    """Duration set in a timedelta or in seconds if using an integer."""
    project_id: Optional[int] = field(default=None)
    start: Optional[datetime] = field(default=None)
    start_date: Optional[date] = field(default=None)
    """Start date in YYYY-MM-DD format. If start is present start_date is ignored."""
    stop: Optional[datetime] = field(default=None)
    tag_action: Optional[Literal["add", "remove"]] = field(default=None)
    """Options are *add* or *remove*. Will default to *add* if not set and tags are present."""
    tag_ids: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    shared_with_user_ids: list[int] = field(default_factory=list)
    created_with: str = field(default="toggl-api-wrapper")

    def format_body(self, workspace_id: int) -> dict:  # noqa: C901
        headers = {
            "workspace_id": self.workspace_id if self.workspace_id else workspace_id,
            "created_with": self.created_with,
            "description": self.description,
        }

        if self.duration:
            dur = self.duration.total_seconds() if isinstance(self.duration, timedelta) else self.duration
            headers["duration"] = dur
        elif not self.stop and self.start:
            headers["duration"] = -1

        if self.project_id:
            headers["project_id"] = self.project_id

        if self.start:
            headers["start"] = format_iso(self.start)
        elif self.start_date:
            headers["start_date"] = format_iso(self.start_date)

        if self.stop:
            headers["stop"] = format_iso(self.stop)

        if self.tag_ids:
            headers["tag_ids"] = self.tag_ids

        if self.tags:
            headers["tags"] = self.tags

        if self.tag_action:
            headers["tag_action"] = self.tag_action
        elif self.tag_ids or self.tags and not self.tag_action:
            headers["tag_action"] = "add"

        return headers


class TrackerEndpoint(TogglCachedEndpoint):
    TRACKER_ALREADY_STOPPED: Final[int] = 409

    def edit_tracker(
        self,
        tracker: TogglTracker,
        body: TrackerBody,
    ) -> Optional[TogglTracker]:
        data = self.request(
            f"/{tracker.id}",
            method=RequestMethod.PUT,
            body=body.format_body(self.workspace_id),
            refresh=True,
        )
        if not isinstance(data, self.model):
            return None

        return data

    def delete_tracker(self, tracker: TogglTracker) -> None:
        try:
            self.request(
                f"/{tracker.id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != self.NOT_FOUND:
                raise
        self.cache.delete_entries(tracker)
        self.cache.commit()

    def stop_tracker(self, tracker: TogglTracker) -> Optional[TogglTracker]:
        try:
            return self.request(  # type: ignore[return-value]
                f"/{tracker.id}/stop",
                method=RequestMethod.PATCH,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != self.TRACKER_ALREADY_STOPPED:
                raise
        return None

    def add_tracker(self, body: TrackerBody) -> Optional[TogglTracker]:
        return self.request(
            "",
            method=RequestMethod.POST,
            body=body.format_body(self.workspace_id),
            refresh=True,
        )  # type: ignore[return-value]

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/time_entries"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
