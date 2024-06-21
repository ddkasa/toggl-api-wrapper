from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Final, Literal, Optional

from httpx import HTTPStatusError

from toggl_api.modules.meta import RequestMethod, TogglCachedEndpoint
from toggl_api.modules.models import TogglTracker
from toggl_api.utility import format_iso


@dataclass
class TrackerBody:
    """JSON body dataclass for PUT, POST & PATCH requests."""

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
    """Options are *add* or *remove*. Will default to *add* when editing a
    tracker. Otherwise ignored."""
    tag_ids: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    shared_with_user_ids: list[int] = field(default_factory=list)
    created_with: str = field(default="toggl-api-wrapper")

    def format_body(self, workspace_id: int) -> dict[str, Any]:
        """Formats the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            workspace_id (int): Alternate Workspace ID for the request
                if the body does not contain a workspace_id.

        Returns:
            dict[str, Any]: JSON compatible formatted body.
        """
        headers = {
            "workspace_id": self.workspace_id or workspace_id,
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
        return headers


class TrackerEndpoint(TogglCachedEndpoint):
    TRACKER_ALREADY_STOPPED: Final[int] = 409

    def edit_tracker(
        self,
        tracker: TogglTracker,
        body: TrackerBody,
    ) -> Optional[TogglTracker]:
        """Edit an existing tracker."""
        if (body.tag_ids or body.tags) and not body.tag_action:
            body.tag_action = "add"

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
        """Delete tracker from Toggl.

        Args:
            tracker: Tracker object with ID to delete.

        Returns:
            None: If the tracker was deleted or not found at all.
        """
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
        """Stops a running tracker.

        Args:
            tracker: Tracker object with IP to stop.

        Returns:
            TogglTracker: If the tracker was stopped or if the tracker wasn't
                running it will return None.
        """
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
        """Add a new tracker.

        Args:
            body: Body of the request. Description must be set. If start date
                is not set it will be set to current time with duration set
                to -1 for a running tracker.

        Raises:
            ValueError: Description must be set in order to create a new
                tracker.

        Returns:
            TogglTracker: The tracker that was created.
        """
        if not isinstance(body.description, str):
            msg = "Description must be set in order to create a tracker!"
            raise ValueError(msg)  # noqa: TRY004

        if body.start is None and body.start_date is None:
            body.start = datetime.now(tz=timezone.utc)
            if body.stop is None:
                body.duration = -1

        body.tag_action = None

        return self.request(
            "",
            method=RequestMethod.POST,
            body=body.format_body(self.workspace_id),
            refresh=True,
        )  # type: ignore[return-value]

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/time_entries"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
