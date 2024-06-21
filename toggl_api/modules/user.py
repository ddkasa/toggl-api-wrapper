from datetime import date, datetime
from typing import Final, Optional

from httpx import HTTPError, HTTPStatusError

from .meta import TogglCachedEndpoint
from .models import TogglTracker


class UserEndpoint(TogglCachedEndpoint):
    TRACKER_NOT_RUNNING: Final[int] = 405

    def current_tracker(self, *, refresh: bool = True) -> Optional[TogglTracker]:
        """Get current running tracker. Returns None if no tracker is running."""

        try:
            response = self.request("time_entries/current", refresh=refresh)
        except HTTPStatusError as err:
            if err.response.status_code == self.TRACKER_NOT_RUNNING:
                return None
            raise

        return response if isinstance(response, TogglTracker) else None

    def get_trackers(  # noqa: PLR0913
        self,
        since: Optional[int | datetime] = None,
        before: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        *,
        refresh: bool = False,
    ) -> list[TogglTracker]:
        """Get a set of trackers depending on specified parameters.

        Args:
            since: Get entries modified since this date using UNIX timestamp,
                including deleted ones.
            before: Get entries with start time, before given date (YYYY-MM-DD)
                or with time in RFC3339 format.
            start_date: Get entries with start time, from start_date YYYY-MM-DD
                or with time in RFC3339 format. To be used with end_date.
            end_date: Get entries with start time, until end_date YYYY-MM-DD or
                with time in RFC3339 format. To be used with start_date.
            refresh: Whether to refresh the cache or not.

        Returns:
            list[TogglTracker]: List of TogglTracker objects that are within
                specified parameters. Empty if none matched.
        """

        params = "time_entries"
        if since and before:
            params = f"?since={since}&before={before}"
        elif start_date and end_date:
            params = f"?start_date={start_date}&end_date={end_date}"
        response = self.request(params, refresh=refresh)

        # TODO: Need to filter cached trackers.
        # TODO: Implement sorting of trackers.

        return response if isinstance(response, list) else []  # type: ignore[return-value]

    def get_tracker(
        self,
        tracker_id: int | TogglTracker,
        *,
        refresh: bool = False,
    ) -> Optional[TogglTracker]:
        """Get a single tracker by ID.

        Args:
            tracker_id: ID of the tracker to get.
            refresh: Whether to refresh the cache or not.

        Returns:
            TogglTracker | None: TogglTracker object or None if not found.
        """
        if isinstance(tracker_id, TogglTracker):
            tracker_id = tracker_id.id

        if not refresh:
            tracker = self.cache.find_entry({"id": tracker_id})
            if isinstance(tracker, TogglTracker):
                return tracker
            refresh = True
        try:
            response = self.request(
                f"time_entries/{tracker_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if err.response.status_code == self.NOT_FOUND:
                return None
            raise

        return response  # type: ignore[return-value]

    def check_authentication(self) -> bool:
        """Check if user is correctly authenticated with the Toggl API."""
        try:
            TogglCachedEndpoint.request(self, "logged")
        except HTTPError:
            return False

        return True

    @property
    def endpoint(self) -> str:
        return "me/"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
