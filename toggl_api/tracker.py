from __future__ import annotations

import logging
import math
import warnings
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Final, Literal, NamedTuple, Optional, TypedDict

from httpx import HTTPStatusError, codes

from toggl_api._exceptions import NamingError
from toggl_api.meta import BaseBody, RequestMethod, TogglCache, TogglCachedEndpoint
from toggl_api.models import TogglTracker
from toggl_api.utility import format_iso

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api import TogglWorkspace
    from toggl_api.meta import TogglCache


log = logging.getLogger("toggl-api-wrapper.endpoint")


class BulkEditParameter(TypedDict):
    op: Literal["add", "remove", "replace"]
    path: str
    value: Any


class Edits(NamedTuple):
    successes: list[int]
    failures: list[int]


@dataclass
class TrackerBody(BaseBody):
    """JSON body dataclass for PUT, POST & PATCH requests.

    Examples:
        >>> TrackerBody(description="What a wonderful tracker description!", project_id=2123132)
        TrackerBody(description="What a wonderful tracker description!", project_id=2123132)
    """

    description: Optional[str] = field(
        default=None,
        metadata={"endpoints": frozenset(("add", "edit", "bulk_edit"))},
    )
    """Description of the a tracker. Refers to the name of a model within the wrapper."""
    duration: Optional[int | timedelta] = field(
        default=None,
        metadata={"endpoints": ("add", "edit")},
    )
    """Duration set in a timedelta or in seconds if using an integer."""
    project_id: Optional[int] = field(
        default=None,
        metadata={"endpoints": ("add", "edit")},
    )
    """Project the tracker belongs. If the value == -1 its marked for removal."""
    start: Optional[datetime] = field(
        default=None,
        metadata={"endpoints": ("add", "edit", "bulk_edit")},
    )
    """Start time of the tracker. If using `bulk_edit` endpoint the date is only used."""
    start_date: Optional[date] = field(default=None)
    stop: Optional[datetime] = field(
        default=None,
        metadata={"endpoints": ("add", "edit", "bulk_edit")},
    )
    """Stop time of a tracker. If using `bulk_edit` endpoint the date is only used."""
    tag_action: Optional[Literal["add", "remove"]] = field(
        default=None,
        metadata={"endpoints": ("add", "edit", "bulk_edit")},
    )
    """Options are *add* or *remove*. Will default to *add* when editing a
    tracker. Otherwise ignored."""
    tag_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": ("add", "edit")},
    )
    """Tag integer ids in a list. Tag action decides what to do with them."""
    tags: list[str] = field(
        default_factory=list,
        metadata={"endpoints": ("add", "edit", "bulk_edit")},
    )
    """Names of tags to assocciate a tracker with. Tag action decides what to do with them."""
    shared_with_user_ids: list[int] = field(
        default_factory=list,
        metadata={"endpoints": ("add", "edit")},
    )
    """Which user to share the tracker with."""
    created_with: str = field(
        default="toggl-api-wrapper",
        metadata={"endpoints": ("add", "edit")},
    )

    def __post_init__(self) -> None:
        if self.start_date is not None:
            warnings.warn(
                'DEPRECATED: "start_date" will be removed. Use "start" parameter instead!',
                DeprecationWarning,
                stacklevel=3,
            )
            if self.start is None:
                self.start = datetime(
                    self.start_date.year,
                    self.start_date.month,
                    self.start_date.day,
                    tzinfo=timezone.utc,
                )

    def _format_bulk_edit(self) -> list[BulkEditParameter]:
        params: list[BulkEditParameter] = []

        if self.description:
            params.append(
                {
                    "op": "replace",
                    "path": "/description",
                    "value": self.description,
                },
            )

        if self.tags and self.tag_action:
            params += [{"op": self.tag_action, "path": "/tags", "value": self.tags}]

        if self.start:
            start = self.start.date() if isinstance(self.start, datetime) else self.start
            params.append({"op": "replace", "path": "/start", "value": format_iso(start)})

            if self.stop and self.start > self.stop:
                log.warning("Start is after the stop time! Ignoring 'stop' parameter!")
                self.stop = None

        if self.stop:
            stop = self.stop.date() if isinstance(self.stop, datetime) else self.stop
            params.append({"op": "replace", "path": "/stop", "value": format_iso(stop)})

        return params

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

        if self.project_id == -1:
            body["project_id"] = None
        elif self.project_id is not None:
            body["project_id"] = self.project_id

        if self.start:
            body["start"] = format_iso(self.start)

        if self.stop:
            body["stop"] = format_iso(self.stop)

        if self.tag_ids:
            body["tag_ids"] = self.tag_ids

        if self.tags:
            body["tags"] = self.tags

        if self.tag_action:
            body["tag_action"] = self.tag_action

        return body


class TrackerEndpoint(TogglCachedEndpoint[TogglTracker]):
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

    Params:
        workspace_id: The workspace the Toggl trackers belong to.
        auth: Authentication for the client.
        cache: Where to cache trackers.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    TRACKER_ALREADY_STOPPED: Final[int] = 409

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: TogglCache[TogglTracker],
        *,
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(0, auth, cache, timeout=timeout, re_raise=re_raise, retries=retries)
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    def edit(
        self,
        tracker: TogglTracker | int,
        body: TrackerBody,
        *,
        meta: bool = False,
    ) -> TogglTracker:
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
            meta: Should the response contain data for meta entities.

        Raises:
            HTTPStatusError: For anything thats not a *ok* status code.

        Returns:
            A new model if successful else None.
        """
        if (body.tag_ids or body.tags) and not body.tag_action:
            body.tag_action = "add"

        if isinstance(tracker, TogglTracker):
            tracker = tracker.id

        return self.request(
            f"/{tracker}",
            method=RequestMethod.PUT,
            body=body.format("edit", workspace_id=self.workspace_id, meta=meta),
            refresh=True,
        )

    def _bulk_edit(
        self,
        trackers: list[int],
        body: list[BulkEditParameter],
    ) -> dict[str, list[int]]:
        url = "/" + ",".join([str(t) for t in trackers])

        return self.request(
            url,
            body=body,
            refresh=True,
            method=RequestMethod.PATCH,
            raw=True,
        ).json()

    def bulk_edit(
        self,
        *trackers: int | TogglTracker,
        body: TrackerBody,
    ) -> Edits:
        """Bulk edit multiple trackers at the same time.

        Patch will be executed partially when there are errors with some records.
        No transaction, no rollback.

        There is a limit of editing 100 trackers at the same time, so the
        method will make multiple calls if the count exceeds that limit.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries/#patch-bulk-editing-time-entries)

        Examples:
            >>> body = TrackerBody(description="All these trackers belong to me!")
            >>> tracker_endpoint.bulk_edit(1235151, 214124, body)
            Edits(successes=[1235151, 214124], failures=[])

        Args:
            trackers: All trackers that need to be edited.
            body: The parameters that need to be edited.

        Raises:
            HTTPStatusError: For anything thats not a *ok* status code.

        Returns:
            Successeful or failed ids editing the trackers.
        """
        tracker_ids = [t if isinstance(t, int) else t.id for t in trackers]
        requests = math.ceil(len(tracker_ids) / 100)
        success: list[int]
        failure: list[int]
        success, failure = [], []

        fmt_body = body._format_bulk_edit()  # noqa: SLF001
        for i in range(requests):
            edit = self._bulk_edit(tracker_ids[100 * i : 100 + (100 * i)], fmt_body)
            success.extend(edit["success"])
            failure.extend(edit["failure"])

        return Edits(success, failure)

    def delete(self, tracker: TogglTracker | int) -> None:
        """Delete a tracker from Toggl.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#delete-timeentries)

        Examples:
            >>> tracker_endpoint.delete(58687684)
            None

        Args:
            tracker: Tracker object with ID to delete.

        Raises:
            HTTPStatusError: If anything thats not a '404' or 'ok' code is returned.

        Returns:
            If the tracker was deleted or not found at all.
        """
        tracker_id = tracker if isinstance(tracker, int) else tracker.id
        try:
            self.request(f"/{tracker_id}", method=RequestMethod.DELETE, refresh=True)
        except HTTPStatusError as err:
            if self.re_raise or err.response.status_code != codes.NOT_FOUND:
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
           If the tracker was stopped or if the tracker wasn't running it will return None.
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
            if self.re_raise or err.response.status_code != self.TRACKER_ALREADY_STOPPED:
                raise
            log.warning("Tracker with id %s was already stopped!", tracker)
        return None

    def add(self, body: TrackerBody) -> TogglTracker:
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
            HTTPStatusError: For anything that wasn't an *ok* status code.
            NamingError: Description must be set in order to create a new tracker.

        Returns:
            The tracker that was created.
        """
        if not isinstance(body.description, str):
            warnings.warn(
                "DEPRECATED: 'TypeError' is being swapped for a 'NamingError'.",
                DeprecationWarning,
                stacklevel=2,
            )
            msg = "Description must be set in order to create a tracker!"
            raise TypeError(msg)
        if not body.description:
            msg = "Description must be set in order to create a tracker!"
            raise NamingError(msg)

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
