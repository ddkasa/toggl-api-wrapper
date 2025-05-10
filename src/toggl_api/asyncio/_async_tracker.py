from __future__ import annotations

import asyncio
import logging
import math
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Final, cast

from httpx import AsyncClient, HTTPStatusError, Response, codes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toggl_api import TogglTracker, TrackerBody
from toggl_api._exceptions import DateTimeError, NamingError
from toggl_api._tracker import BulkEditParameter, Edits
from toggl_api.meta import RequestMethod
from toggl_api.utility import format_iso, get_timestamp

from ._async_endpoint import TogglAsyncCachedEndpoint

if TYPE_CHECKING:
    from httpx import BasicAuth
    from sqlalchemy.engine import ScalarResult
    from sqlalchemy.sql.expression import ColumnElement

    from toggl_api import TogglWorkspace

    from ._async_sqlite_cache import AsyncSqliteCache


log = logging.getLogger("toggl-api-wrapper.endpoint")


class AsyncTrackerEndpoint(TogglAsyncCachedEndpoint[TogglTracker]):
    """Endpoint for modifying and creating trackers.

    [Official Documentation](https://engineering.toggl.com/docs/api/time_entries)

    Examples:
        >>> tracker_endpoint = TrackerEndpoint(324525, BasicAuth(...), AsyncSqliteCache(Path("cache")))

        >>> body = TrackerBody(description="What a wonderful tracker description!", project_id=2123132)
        >>> await tracker_endpoint.add(body)
        TogglTracker(id=58687689, name="What a wonderful tracker description!", project=2123132, ...)

        >>> await tracker_endpoint.delete(tracker)
        None

    Params:
        workspace_id: The workspace the Toggl trackers belong to.
        auth: Authentication for the client.
        cache: Where to cache trackers. Currently async only supports SQLite.
        client: Optional async client to be passed to be used for requests.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    MODEL = TogglTracker
    TRACKER_ALREADY_STOPPED: Final[int] = codes.CONFLICT
    TRACKER_NOT_RUNNING: Final[int] = codes.METHOD_NOT_ALLOWED

    def __init__(
        self,
        workspace_id: int | TogglWorkspace,
        auth: BasicAuth,
        cache: AsyncSqliteCache[TogglTracker] | None = None,
        *,
        client: AsyncClient | None = None,
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(
            auth,
            cache,
            client=client,
            timeout=timeout,
            re_raise=re_raise,
            retries=retries,
        )
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    async def _current_refresh(self, tracker: TogglTracker | None) -> None:
        if self.cache and tracker is None:
            running = await self._find_running()
            await asyncio.gather(
                *[self.get(tracker, refresh=True) for tracker in running],
            )

    async def _find_running(self) -> ScalarResult[TogglTracker]:
        stmt = select(TogglTracker).filter(
            cast("ColumnElement[bool]", TogglTracker.stop is None),
        )

        cache = cast("AsyncSqliteCache[TogglTracker]", self.cache)
        async with AsyncSession(
            cache.database,
            expire_on_commit=False,
        ) as session:
            return (await session.execute(stmt)).scalars()

    async def current(self, *, refresh: bool = True) -> TogglTracker | None:
        """Get current running tracker. Returns None if no tracker is running.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#get-get-current-time-entry)

        Examples:
            >>> await tracker_endpoint.current()
            None

            >>> await tracker_endpoint.current(refresh=True)
            TogglTracker(...)

        Args:
            refresh: Whether to check the remote API for running trackers.
                If 'refresh' is True it will check if there are any other running
                trackers and update if the 'stop' attribute is None.

        Raises:
            HTTPStatusError: If the request is not a success or any error that's
                not a '405' status code.

        Returns:
            A model from cache or the API. None if nothing is running.
        """
        if self.cache and not refresh:
            return (await self._find_running()).first()

        try:
            response = await self.request(
                "me/time_entries/current",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == self.TRACKER_NOT_RUNNING:
                log.warning("No tracker is currently running!")
                response = None
            else:
                raise

        await self._create_task(
            self._current_refresh(cast("TogglTracker | None", response)),
            name="current",
        )

        return cast("TogglTracker | None", response)

    async def _collect_cache(
        self,
        since: int | datetime | None = None,
        before: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> ScalarResult[TogglTracker]:
        stmt = select(TogglTracker)
        if since or before:
            if since:
                since = datetime.fromtimestamp(since, tz=timezone.utc) if isinstance(since, int) else since
                stmt = stmt.filter(
                    cast("ColumnElement[bool]", TogglTracker.timestamp > since),
                )
            if before:
                stmt = stmt.filter(
                    cast("ColumnElement[bool]", TogglTracker.start < before),
                )

        elif start_date and end_date:
            stmt = stmt.filter(
                cast("ColumnElement[bool]", TogglTracker.start > start_date),
                cast("ColumnElement[bool]", TogglTracker.start < end_date),
            )
        cache = cast("AsyncSqliteCache[TogglTracker]", self.cache)
        async with AsyncSession(
            cache.database,
            expire_on_commit=False,
        ) as session:
            return (await session.execute(stmt)).scalars()

    async def collect(
        self,
        since: int | datetime | None = None,
        before: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        *,
        refresh: bool = False,
    ) -> list[TogglTracker]:
        """Get a set of trackers depending on specified parameters.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#get-timeentries)

        Missing meta and include_sharing query flags not supported by wrapper at
        the moment.

        Examples:
            >>> await tracker_ep.collect(since=17300032362, before=date(2024, 11, 27))

            >>> await tracker_ep.collect(refresh=True)

            >>> await tracker_ep.collect(start_date=date(2024, 11, 27), end_date=date(2024, 12, 27))

        Args:
            since: Get entries modified since this date using UNIX timestamp.
                Includes deleted ones if refreshing.
            before: Get entries with start time, before given date (YYYY-MM-DD)
                or with time in RFC3339 format.
            start_date: Get entries with start time, from start_date YYYY-MM-DD
                or with time in RFC3339 format. To be used with end_date.
            end_date: Get entries with start time, until end_date YYYY-MM-DD or
                with time in RFC3339 format. To be used with start_date.
            refresh: Whether to refresh the cache or not.

        Raises:
            DateTimeError: If the dates are not in the correct ranges.
            HTTPStatusError: If the request is not a successful status code.

        Returns:
           List of TogglTracker objects that are within specified parameters.
                Empty if none is matched.
        """
        if start_date and end_date:
            if end_date < start_date:
                msg = "end_date must be after the start_date!"
                raise DateTimeError(msg)
            if start_date > datetime.now(tz=timezone.utc):
                msg = "start_date must not be earlier than the current date!"
                raise DateTimeError(msg)

        if not refresh:
            return list(
                await self._collect_cache(since, before, start_date, end_date),
            )

        params = "me/time_entries"
        if since or before:
            if since:
                params += f"?since={get_timestamp(since)}"

            if before:
                params += "&" if since else "?"
                params += f"before={format_iso(before)}"

        elif start_date and end_date:
            params += f"?start_date={format_iso(start_date)}&end_date={format_iso(end_date)}"

        response = await self.request(params, refresh=refresh)

        return cast("list[TogglTracker]", response)

    async def get(
        self,
        tracker_id: int | TogglTracker,
        *,
        refresh: bool = False,
    ) -> TogglTracker | None:
        """Get a single tracker by ID.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#get-get-a-time-entry-by-id)

        Args:
            tracker_id: ID of the tracker to get.
            refresh: Whether to refresh the cache or not.

        Raises:
            HTTPStatusError: If anything thats not a *ok* or *404* status code
                is returned.

        Returns:
            TogglTracker object or None if not found.
        """
        if isinstance(tracker_id, TogglTracker):
            tracker_id = tracker_id.id

        if self.cache and not refresh:
            return await self.cache.find(tracker_id)

        try:
            response = await self.request(
                f"me/time_entries/{tracker_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                log.warning("Tracker with id %s does not exist!", tracker_id)
                return None
            raise

        return cast("TogglTracker", response)

    async def edit(
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
            >>> await tracker_endpoint.edit(58687684, body)
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

        response = await self.request(
            f"{self.endpoint}/{tracker}",
            method=RequestMethod.PUT,
            body=body.format(
                "edit",
                workspace_id=self.workspace_id,
                meta=meta,
            ),
            refresh=True,
        )

        return cast("TogglTracker", response)

    async def _bulk_edit(
        self,
        trackers: list[int],
        body: list[BulkEditParameter],
    ) -> dict[str, list[int]]:
        response = await self.request(
            f"{self.endpoint}/" + ",".join([str(t) for t in trackers]),
            body=body,
            refresh=True,
            method=RequestMethod.PATCH,
            raw=True,
        )
        return cast("dict[str, list[int]]", cast("Response", response).json())

    async def bulk_edit(
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
            >>> await tracker_endpoint.bulk_edit(1235151, 214124, body)
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
            edit = await self._bulk_edit(
                tracker_ids[100 * i : 100 + (100 * i)],
                fmt_body,
            )
            success.extend(edit["success"])
            failure.extend(edit["failure"])

        return Edits(success, failure)

    async def delete(self, tracker: TogglTracker | int) -> None:
        """Delete a tracker from Toggl.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#delete-timeentries)

        Examples:
            >>> await tracker_endpoint.delete(58687684)
            None

        Args:
            tracker: Tracker object with ID to delete.

        Raises:
            HTTPStatusError: If anything thats not a '404' or 'ok' code is returned.
        """
        tracker_id = tracker if isinstance(tracker, int) else tracker.id
        try:
            await self.request(
                f"{self.endpoint}/{tracker_id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if self.re_raise or err.response.status_code != codes.NOT_FOUND:
                raise
            log.warning(
                "Tracker with id %s was either already deleted or did not exist in the first place!",
                tracker_id,
            )
        if self.cache is None:
            return

        if isinstance(tracker, int):
            trk = await self.cache.find(tracker)
            if not isinstance(trk, TogglTracker):
                return
            tracker = trk

        await self.cache.delete(tracker)

    async def stop(self, tracker: TogglTracker | int) -> TogglTracker | None:
        """Stop the current running tracker.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#patch-stop-timeentry)

        Examples:
            >>> await tracker_endpoint.stop(58687684)
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
            response = await self.request(
                f"{self.endpoint}/{tracker}/stop",
                method=RequestMethod.PATCH,
                refresh=True,
            )
            return cast("TogglTracker", response)
        except HTTPStatusError as err:
            if self.re_raise or err.response.status_code != self.TRACKER_ALREADY_STOPPED:
                raise
            log.warning("Tracker with id %s was already stopped!", tracker)
        return None

    async def add(self, body: TrackerBody) -> TogglTracker:
        """Add a new tracker.

        This endpoint always hit the external API in order to keep trackers consistent.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#post-timeentries)

        Examples:
            >>> body = TrackerBody(description="Tracker description!", project_id=2123132)
            >>> await tracker_endpoint.edit(body)
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
        if not body.description:
            msg = "Description must be set in order to create a tracker!"
            raise NamingError(msg)

        if body.start is None:
            body.start = datetime.now(tz=timezone.utc)
            log.info(
                "Body is missing a start. Setting to %s...",
                body.start,
                extra={"body": body},
            )
            if body.stop is None:
                body.duration = -1

        body.tag_action = "add"

        response = await self.request(
            self.endpoint,
            method=RequestMethod.POST,
            body=body.format("add", workspace_id=self.workspace_id),
            refresh=True,
        )
        return cast("TogglTracker", response)

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/time_entries"
