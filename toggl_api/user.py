from __future__ import annotations

import logging
import warnings
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Final, cast

import httpx
from httpx import HTTPStatusError, Response, codes

from toggl_api import Comparison, TogglQuery
from toggl_api._exceptions import DateTimeError

from .meta import TogglCachedEndpoint, TogglEndpoint
from .models import TogglTracker
from .utility import format_iso, get_timestamp

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api.models.models import TogglWorkspace

    from .meta import TogglCache

log = logging.getLogger("toggl-api-wrapper.endpoint")


class UserEndpoint(TogglCachedEndpoint[TogglTracker]):
    """Endpoint for retrieving and fetching trackers with GET requests.

    See the [TrackerEndpoint][toggl_api.TrackerEndpoint] for modifying trackers.

    [Official Documentation](https://engineering.toggl.com/docs/api/me)

    Params:
        workspace_id: The workspace the Toggl trackers belong to.
        auth: Authentication for the client.
        cache: Cache object where trackers are stored.
        timeout: How long it takes for the client to timeout. Keyword Only.
            Defaults to 10 seconds.
        re_raise: Whether to raise all HTTPStatusError errors and not handle them
            internally. Keyword Only.
        retries: Max retries to attempt if the server returns a *5xx* status_code.
            Has no effect if re_raise is `True`. Keyword Only.
    """

    MODEL = TogglTracker
    TRACKER_NOT_RUNNING: Final[int] = codes.METHOD_NOT_ALLOWED

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

    def _current_refresh(self, tracker: TogglTracker | None) -> None:
        if tracker is None:
            for t in self.cache.query(TogglQuery("stop", None)):
                try:
                    self.get(t, refresh=True)
                except HTTPStatusError:
                    log.exception("%s")
                    return

    def current(self, *, refresh: bool = True) -> TogglTracker | None:
        """Get current running tracker. Returns None if no tracker is running.

        [Official Documentation](https://engineering.toggl.com/docs/api/time_entries#get-get-current-time-entry)

        Examples:
            >>> user_endpoint.current()
            None

            >>> user_endpoint.current(refresh=True)
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

        if not refresh:
            query = list(self.cache.query(TogglQuery("stop", None)))
            return query[0] if query else None

        try:
            response = self.request("/time_entries/current", refresh=refresh)
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == self.TRACKER_NOT_RUNNING:
                log.warning("No tracker is currently running!")
                response = None
            else:
                raise

        self._current_refresh(cast(TogglTracker | None, response))

        return response if isinstance(response, TogglTracker) else None

    def _collect_cache(
        self,
        since: int | datetime | None = None,
        before: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
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
            >>> collect(since=17300032362, before=date(2024, 11, 27))

            >>> collect(refresh=True)

            >>> collect(start_date=date(2024, 11, 27), end_date=date(2024, 12, 27))

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
            return self._collect_cache(since, before, start_date, end_date)

        params = "/time_entries"
        if since or before:
            if since:
                params += f"?since={get_timestamp(since)}"

            if before:
                params += "&" if since else "?"
                params += f"before={format_iso(before)}"

        elif start_date and end_date:
            params += f"?start_date={format_iso(start_date)}&end_date={format_iso(end_date)}"

        response = self.request(params, refresh=refresh)

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

        Raises:
            HTTPStatusError: If anything thats not a *ok* or *404* status code
                is returned.

        Returns:
            TogglTracker object or None if not found.
        """
        if isinstance(tracker_id, TogglTracker):
            tracker_id = tracker_id.id

        if not refresh:
            return self.cache.find_entry({"id": tracker_id})

        try:
            response = self.request(
                f"/time_entries/{tracker_id}",
                refresh=refresh,
            )
        except HTTPStatusError as err:
            if not self.re_raise and err.response.status_code == codes.NOT_FOUND:
                log.warning("Tracker with id %s does not exist!", tracker_id)
                return None
            raise

        return cast(TogglTracker, response)

    def check_authentication(self) -> bool:
        """Check if user is correctly authenticated with the Toggl API.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-logged)
        """
        warnings.warn(
            (
                "DEPRECATED: 'check_authentication' is being removed. "
                "Use the static method 'verify_authentication instead!"
            ),
            stacklevel=3,
        )
        try:
            TogglEndpoint.request(self, "/logged")
        except HTTPStatusError as err:
            log.critical("Failed to verify authentication!")
            log.exception("%s")
            if err.response.status_code != codes.FORBIDDEN:
                raise

            return False

        return True

    @staticmethod
    def verify_authentication(auth: BasicAuth) -> bool:
        """Check if user is correctly authenticated with the Toggl API.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-logged)

        Examples:
            >>> UserEndpoint.verify_authentication(auth)
            True

            >>> auth = generate_authentication()
            >>> UserEndpoint.verify_authentication(auth)
            True

        Args:
            auth: Basic authentication object either created manually or one
                of the provided authentication utilities.

        Raises:
            HTTPStatusError: If anything that is an error that is not a FORBIDDEN code.

        Returns:
            True if successfully verified authentication else False.
        """
        try:
            httpx.get(TogglEndpoint.BASE_ENDPOINT + "me/logged", auth=auth).raise_for_status()
        except HTTPStatusError as err:
            log.critical("Failed to verify authentication!")
            log.exception("%s")
            if err.response.status_code != codes.FORBIDDEN:
                raise

            return False

        return True

    def get_details(self) -> dict[str, Any]:
        """Returns details for the current user.

        [Official Documentation](https://engineering.toggl.com/docs/api/me#get-me)

        Raises:
            HTTPStatusError: If the request is not a successful status code.

        Returns:
            User details in a raw dictionary.
        """
        return cast(Response, TogglEndpoint.request(self, "", raw=True)).json()

    @property
    def endpoint(self) -> str:
        return "me"
