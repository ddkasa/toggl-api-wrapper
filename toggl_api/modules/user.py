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

        # Need to filter cached trackers.

        return response if isinstance(response, list) else []  # type: ignore[return-value]

    def get_tracker(
        self,
        tracker_id: int,
        *,
        refresh: bool = False,
    ) -> Optional[TogglTracker]:
        """Get a single tracker by ID."""
        cache = self.load_cache() if not refresh else None
        if isinstance(cache, list):
            for item in cache:
                if item.id == tracker_id:
                    return item  # type: ignore[return-value]

        try:
            response = self.request(
                f"time_entries/{tracker_id}",
                refresh=refresh,
            )
        except HTTPError:
            response = None

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
