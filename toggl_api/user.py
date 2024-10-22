import logging
from datetime import date, datetime, timezone
from typing import Final, Optional

from httpx import HTTPError, HTTPStatusError

from toggl_api import Comparison, TogglQuery

from .meta import TogglCachedEndpoint
from .models import TogglTracker
from .utility import format_iso

log = logging.getLogger("toggl-api-wrapper.endpoint")


class UserEndpoint(TogglCachedEndpoint):
    """Endpoint for retrieving and fetching trackers with GET requests.

    See the [TrackerEndpoint][toggl_api.TrackerEndpoint] for modifying trackers.

    [Official Documentation](https://engineering.toggl.com/docs/api/me)
    """

    TRACKER_NOT_RUNNING: Final[int] = 405

    def current(self, *, refresh: bool = True) -> TogglTracker | None:
        """Get current running tracker. Returns None if no tracker is running.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#get-get-current-time-entry)
        """

        if not refresh:
            query = list(self.cache.query(TogglQuery("stop", None)))
            return query[0] if query else None  # type: ignore[return-value]

        try:
            response = self.request("time_entries/current", refresh=refresh)
        except HTTPStatusError as err:
            if err.response.status_code == self.TRACKER_NOT_RUNNING:
                log.warning("No tracker is currently running!")
                return None
            raise

        return response if isinstance(response, TogglTracker) else None

    def _collect_cache(
        self,
        since: Optional[int | datetime] = None,
        before: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[TogglTracker]:
        cache: list[TogglTracker] = []
        if since or before:
            queries: list[TogglQuery[date]] = []

            if since:
                since = datetime.fromtimestamp(since, tz=timezone.utc) if isinstance(since, int) else since
                queries.append(TogglQuery("timestamp", since, Comparison.GREATER_THEN))

            if before:
                queries.append(TogglQuery("start", before, Comparison.LESS_THEN))

            cache.extend(self.query(*queries))

        elif start_date and end_date:
            cache.extend(
                self.query(
                    TogglQuery("start", start_date, Comparison.GREATER_THEN_OR_EQUAL),
                    TogglQuery("start", end_date, Comparison.LESS_THEN_OR_EQUAL),
                ),
            )
        else:
            cache.extend(self.load_cache())

        return cache

    def collect(
        self,
        since: Optional[int | datetime] = None,
        before: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        *,
        refresh: bool = False,
    ) -> list[TogglTracker]:
        """Get a set of trackers depending on specified parameters.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#get-timeentries)

        Missing meta and include_sharing query flags not supported by wrapper at
        the moment.

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
            ValueError: If the dates are not in the correct ranges.

        Returns:
            list[TogglTracker]: List of TogglTracker objects that are within
                specified parameters. Empty if none is matched.
        """

        if start_date and end_date:
            if end_date < start_date:
                msg = "end_date must be after the start_date!"
                raise ValueError(msg)
            if start_date > datetime.now(tz=timezone.utc):
                msg = "start_date must not be earlier than the current date!"
                raise ValueError(msg)

        if not refresh:
            return self._collect_cache(since, before, start_date, end_date)

        params = "time_entries"
        if since or before:
            if since:
                format_since = int(since.timestamp()) if isinstance(since, datetime) else since
                params += f"?since={format_since}"

            if before:
                params += "&" if since else "?"
                params += f"before={format_iso(before)}"

        elif start_date and end_date:
            params += f"?start_date={format_iso(start_date)}&end_date={format_iso(end_date)}"

        response = self.request(params)

        return response if isinstance(response, list) else []

    def get(
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

        Returns:
            TogglTracker | None: TogglTracker object or None if not found.
        """
        if isinstance(tracker_id, TogglTracker):
            tracker_id = tracker_id.id

        if not refresh:
            return self.cache.find_entry({"id": tracker_id})  # type: ignore[return-value]

        try:
            response = self.request(
                f"time_entries/{tracker_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if err.response.status_code == self.NOT_FOUND:
                log.warning("Tracker with id %s does not exist!", tracker_id)
                return None
            raise

        return response

    def check_authentication(self) -> bool:
        """Check if user is correctly authenticated with the Toggl API.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-logged)
        """
        try:
            TogglCachedEndpoint.request(self, "logged")
        except HTTPError:
            log.critical("Failed to verify authentication!")
            log.exception("%s")
            return False

        return True

    @property
    def endpoint(self) -> str:
        return "me/"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
