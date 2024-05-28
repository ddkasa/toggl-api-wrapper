from typing import Final, Optional

from httpx import HTTPError, HTTPStatusError

from .meta import TogglCachedEndpoint
from .models import TogglTracker


class UserEndpoint(TogglCachedEndpoint):
    TRACKER_NOT_RUNNING: Final[int] = 405

    def current_tracker(self, *, refresh: bool = True) -> Optional[TogglTracker]:
        url = "time_entries/current"

        try:
            response = self.request(url, refresh=refresh)
        except HTTPStatusError as err:
            if err.response.status_code == self.TRACKER_NOT_RUNNING:
                return None

        return response if isinstance(response, TogglTracker) else None

    def get_trackers(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglTracker]:
        since = kwargs.get("since")  # UNIX Timestamp
        before = kwargs.get("before")  #  YYYY-MM-DD
        start_date = kwargs.get("start_date")  # YYYY-MM-DD or RFC3339
        end_date = kwargs.get("end_date")  # YYYY-MM-DD or RFC3339

        params = "time_entries"
        if since and before:
            params = f"?since={since}&before={before}"
        elif start_date and end_date:
            params = f"?start_date={start_date}&end_date={end_date}"
        response = self.request(params, refresh=refresh)

        return response if isinstance(response, list) else []  # type: ignore[return-value]

    def get_tracker(
        self,
        tracker_id: int,
        *,
        refresh: bool = False,
    ) -> Optional[TogglTracker]:
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
        try:
            TogglCachedEndpoint.request(self, "logged")
        except HTTPError:
            return False

        return True

    @property
    def endpoint(self) -> str:
        return super().endpoint + "me/"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
