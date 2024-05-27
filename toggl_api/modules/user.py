import httpx
from httpx import HTTPError

from .meta import TogglCachedEndpoint
from .models import TogglTracker


class UserEndpoint(TogglCachedEndpoint):
    def current_tracker(self, *, refresh: bool = True) -> TogglTracker | None:
        url = "time_entries/current"

        try:
            response = self.request(url, refresh=refresh)
        except httpx.HTTPError as err:
            tracker_not_running = 405
            if err.response.status_code == tracker_not_running:
                return None

        return response

    def get_trackers(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglTracker] | None:
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

        if response is None:
            return []
        return response

    def get_tracker(
        self,
        tracker_id: int,
        *,
        refresh: bool = False,
    ) -> TogglTracker | None:
        cache = self.load_cache() if not refresh else None
        if isinstance(cache, list):
            for item in cache:
                if item.id == tracker_id:
                    return item  # type: ignore[return-value]

        try:
            response = self.request(f"time_entries/{tracker_id}", refresh=refresh)
        except HTTPError as exc:
            print(exc)
            response = None

        if not isinstance(response, self.model):
            return None

        return response

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
