from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Final, Literal, Optional

from httpx import HTTPStatusError, codes

from toggl_api.meta import BaseBody, RequestMethod, TogglCachedEndpoint
from toggl_api.models import TogglTracker
from toggl_api.utility import format_iso

log = logging.getLogger("toggl-api-wrapper.endpoint")


@dataclass
class TrackerBody(BaseBody):
    """JSON body dataclass for PUT, POST & PATCH requests.

    Examples:
        >>> TrackerBody(description="What a wonderful tracker description!", project_id=2123132)
        TrackerBody(description='What a wonderful tracker description!', project_id=2123132)
    """

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


class TrackerEndpoint(TogglCachedEndpoint):
    """Endpoint for modifying and creating trackers.

    See the [UserEndpoint][toggl_api.UserEndpoint] for _GET_ specific requests.

    [Official Documentation](https://engineering.toggl.com/docs/api/time_entries)

    Examples:
        >>> tracker_endpoint = TrackerEndpoint(324525, BasicAuth(...), JSONCache(Path("cache")))

        >>> body = TrackerBody(description="What a wonderful tracker description!", project_id=2123132)
        >>> tracker = tracker_endpoint.add(body)
        TogglTracker(id=58687689, name="What a wonderful tracker description!", project=2123132, ...)

        >>> tracker_endpoint.delete(tracker)
        None
    """

    TRACKER_ALREADY_STOPPED: Final[int] = 409

    def edit(self, tracker: TogglTracker | int, body: TrackerBody) -> TogglTracker | None:
        """Edit an existing tracker based on the supplied parameters within the body.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#put-timeentries)

        Examples:
            >>> body = TrackerBody(description="What a wonderful tracker description!", project_id=2123132)
            >>> tracker_endpoint.edit(58687684, body)
            TogglTracker(id=58687684, name="What a wonderful tracker description!", project=2123132, ...)

        Args:
            tracker: Target tracker model or id to edit.
            body: Updated content to add.

        Returns:
            TogglTracker | None: A new model if successful else None.
        """
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
            log.error("Failed to edit tracker with the id %s!", tracker, extra={"body": body})
            return None

        return data

    def delete(self, tracker: TogglTracker | int) -> None:
        """Delete a tracker from Toggl.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#delete-timeentries)

        Examples:
            >>> tracker_endpoint.delete(58687684)
            None

        Args:
            tracker: Tracker object with ID to delete.

        Returns:
            None: If the tracker was deleted or not found at all.
        """
        tracker_id = tracker if isinstance(tracker, int) else tracker.id
        try:
            self.request(f"/{tracker_id}", method=RequestMethod.DELETE, refresh=True)
        except HTTPStatusError as err:
            if err.response.status_code != codes.NOT_FOUND:
                raise
            log.warning(
                "Tracker with id %s was either already deleted or did not exist in the first place!",
                tracker_id,
            )

        if isinstance(tracker, int):
            trk = self.cache.find_entry({"id": tracker})
            if not isinstance(trk, TogglTracker):
                return
            tracker = trk

        self.cache.delete_entries(tracker)
        self.cache.commit()

    def stop(self, tracker: TogglTracker | int) -> TogglTracker | None:
        """Stops a running tracker.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#patch-stop-timeentry)

        Examples:
            >>> tracker_endpoint.stop(58687684)
            TogglTracker(id=58687684, name="What a wonderful tracker description!", ...)

        Args:
            tracker: Tracker id to stop. An integer or model.

        Raises:
            HTTPStatusError: For anything thats not 'ok' or a '409' status code.

        Returns:
            TogglTracker | None: If the tracker was stopped or if the tracker
                wasn't running it will return None.
        """
        if isinstance(tracker, TogglTracker):
            tracker = tracker.id
        try:
            return self.request(
                f"/{tracker}/stop",
                method=RequestMethod.PATCH,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != self.TRACKER_ALREADY_STOPPED:
                raise
            log.warning("Tracker with id %s was already stopped!", tracker)
        return None

    def add(self, body: TrackerBody) -> TogglTracker | None:
        """Add a new tracker.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#post-timeentries)

        Examples:
            >>> body = TrackerBody(description="Tracker description!", project_id=2123132)
            >>> tracker_endpoint.edit(body)
            TogglTracker(id=78895400, name="Tracker description!", project=2123132, ...)

        Args:
            body: Body of the request. Description must be set. If start date
                is not set it will be set to current time with duration set
                to -1 for a running tracker.

        Raises:
            ValueError: Description must be set in order to create a new tracker.

        Returns:
            TogglTracker | None: The tracker that was created.
        """
        if not isinstance(body.description, str) or not body.description:
            msg = "Description must be set in order to create a tracker!"
            raise TypeError(msg)

        if body.start is None and body.start_date is None:
            body.start = datetime.now(tz=timezone.utc)
            log.info(
                "Body is missing a start. Setting to %s...",
                body.start,
                extra={"body": body},
            )
            if body.stop is None:
                body.duration = -1

        body.tag_action = "add"

        return self.request(
            "",
            method=RequestMethod.POST,
            body=body.format("add", workspace_id=self.workspace_id),
            refresh=True,
        )

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/time_entries"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
