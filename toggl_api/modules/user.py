from pathlib import Path

from httpx import HTTPError

from .meta import TogglCachedEndpoint, TogglEndpoint
from .models import TogglTracker


class UserCachedEndpoint(TogglCachedEndpoint):
    def current_tracker(self) -> TogglTracker | None:
        url = "time_entries/current"

        response = self.request(url)
        if not isinstance(response, dict):
            return None

        return TogglTracker.from_kwargs(**response)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / "user.json"

    @property
    def endpoint(self) -> str:
        return super().endpoint + "me/"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker


class UserEndpoint(TogglEndpoint):
    def check_authentication(self) -> bool:
        try:
            self.request("logged")
        except HTTPError:
            return False

        return True

    def current_tracker(self) -> TogglTracker | None:
        url = "time_entries/current"

        response = self.request(url)
        if not isinstance(response, dict):
            return None

        return TogglTracker.from_kwargs(**response)

    @property
    def endpoint(self) -> str:
        return super().endpoint + "me/"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
