from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Final, Literal, Optional

from httpx import HTTPStatusError

from toggl_api.modules.meta import BaseBody, RequestMethod, TogglCachedEndpoint
from toggl_api.modules.models import TogglTracker
from toggl_api.utility import format_iso


@dataclass
class TrackerBody(BaseBody):
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

    def __post_init__(self) -> None:
        if self.workspace_id is not None:
            warnings.warn(
                "The 'workspace_id' parameter will be be removed in v1.0.0",
                DeprecationWarning,
                stacklevel=2,
            )

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        """Formats the body for JSON requests.

        Gets called by the endpoint methods before requesting.

        Args:
            endpoint: The endpoints name for filtering purposes.
            body: Additional body arguments that the endpoint requires.

        Returns:
            dict: JSON compatible formatted body.
        """

        body.update(
            {
                "created_with": self.created_with,
                "description": self.description,
            },
        )

        if self.duration:
            dur = self.duration.total_seconds() if isinstance(self.duration, timedelta) else self.duration
            body["duration"] = dur
        elif not self.stop and self.start:
            body["duration"] = -1

        if self.project_id:
            body["project_id"] = self.project_id

        if self.start:
            body["start"] = format_iso(self.start)
        elif self.start_date:
            body["start_date"] = format_iso(self.start_date)

        if self.stop:
            body["stop"] = format_iso(self.stop)

        if self.tag_ids:
            body["tag_ids"] = self.tag_ids

        if self.tags:
            body["tags"] = self.tags

        if self.tag_action:
            body["tag_action"] = self.tag_action

        return body

    def format_body(self, workspace_id: int) -> dict[str, Any]:
        warnings.warn(
            "Deprecated in favour of 'format' method.",
            DeprecationWarning,
            stacklevel=1,
        )
        return self.format("endpoint", workspace_id=workspace_id)


class TrackerEndpoint(TogglCachedEndpoint):
    """Endpoint for modifying and creating trackers.

    See the [UserEndpoint][toggl_api.UserEndpoint] for _GET_ specific requests.
    """

    TRACKER_ALREADY_STOPPED: Final[int] = 409

    def edit(
        self,
        tracker: TogglTracker | int,
        body: TrackerBody,
    ) -> TogglTracker | None:
        """Edit an existing tracker based on the supplied parameters within the body."""
        if (body.tag_ids or body.tags) and not body.tag_action:
            body.tag_action = "add"

        if isinstance(tracker, TogglTracker):
            tracker = tracker.id

        data = self.request(
            f"/{tracker}",
            method=RequestMethod.PUT,
            body=body.format("edit", workspace_id=self.workspace_id),
            refresh=True,
        )
        if not isinstance(data, self.model):
            return None

        return data

    def edit_tracker(
        self,
        tracker: TogglTracker | int,
        body: TrackerBody,
    ) -> TogglTracker | None:
        warnings.warn("Deprecated in favour of 'edit' method.", DeprecationWarning, stacklevel=1)
        return self.edit(tracker, body)

    def delete(self, tracker: TogglTracker | int) -> None:
        """Delete a tracker from Toggl.

        Args:
            tracker: Tracker object with ID to delete.

        Returns:
            None: If the tracker was deleted or not found at all.
        """

        try:
            self.request(
                f"/{tracker if isinstance(tracker, int) else tracker.id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != self.NOT_FOUND:
                raise

        if isinstance(tracker, int):
            tracker = self.cache.find_entry({"id": tracker})  # type: ignore[assignment]
            if not isinstance(tracker, TogglTracker):
                return

        self.cache.delete_entries(tracker)
        self.cache.commit()

    def delete_tracker(self, tracker: TogglTracker | int) -> None:
        warnings.warn(
            "Deprecated in favour of 'delete' method.",
            DeprecationWarning,
            stacklevel=1,
        )
        return self.delete(tracker)

    def stop(self, tracker: TogglTracker | int) -> TogglTracker | None:
        """Stops a running tracker.

        Args:
            tracker: Tracker object with IP to stop.

        Returns:
            TogglTracker: If the tracker was stopped or if the tracker wasn't
                running it will return None.
        """
        if isinstance(tracker, TogglTracker):
            tracker = tracker.id
        try:
            return self.request(  # type: ignore[return-value]
                f"/{tracker}/stop",
                method=RequestMethod.PATCH,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != self.TRACKER_ALREADY_STOPPED:
                raise
        return None

    def stop_tracker(self, tracker: TogglTracker | int) -> TogglTracker | None:
        warnings.warn(
            "Deprecated in favour of 'stop' method.",
            DeprecationWarning,
            stacklevel=1,
        )
        return self.stop(tracker)

    def add(self, body: TrackerBody) -> TogglTracker | None:
        """Add a new tracker.

        Args:
            body: Body of the request. Description must be set. If start date
                is not set it will be set to current time with duration set
                to -1 for a running tracker.

        Raises:
            ValueError: Description must be set in order to create a new
                tracker.

        Returns:
            TogglTracker | None: The tracker that was created.
        """
        if not isinstance(body.description, str):
            msg = "Description must be set in order to create a tracker!"
            raise ValueError(msg)  # noqa: TRY004

        if body.start is None and body.start_date is None:
            body.start = datetime.now(tz=timezone.utc)
            if body.stop is None:
                body.duration = -1

        body.tag_action = "add"

        return self.request(
            "",
            method=RequestMethod.POST,
            body=body.format("add", workspace_id=self.workspace_id),
            refresh=True,
        )  # type: ignore[return-value]

    def add_tracker(self, body: TrackerBody) -> TogglTracker | None:
        warnings.warn(
            "Deprecated in favour of 'add' method.",
            DeprecationWarning,
            stacklevel=1,
        )
        return self.add(body)

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/time_entries"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
