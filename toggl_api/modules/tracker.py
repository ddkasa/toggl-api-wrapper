from pathlib import Path

from httpx import HTTPError

from .meta import RequestMethod, TogglCachedEndpoint, TogglEndpoint
from .models import TogglTracker


class TrackerEndpoint(TogglEndpoint):
    def body_creation(self, **kwargs) -> dict:  # noqa: C901
        headers = {}
        workspace_id = kwargs.get("workspace_id", self.workspace_id)
        headers["workspace_id"] = workspace_id

        created_with = kwargs.get("created_with", "toggl-api-wrapper")
        description = kwargs.get("description")
        duration = kwargs.get("duration")
        project_id = kwargs.get("project_id")
        start = kwargs.get("start")
        start_date = kwargs.get("start_date")
        stop = kwargs.get("stop")
        tag_action = kwargs.get("tag_action")
        tag_ids = kwargs.get("tag_ids")
        tags = kwargs.get("tags")
        shared_with_user_ids = kwargs.get("shared_with_user_ids", [])

        headers["shared_with_user_ids"] = shared_with_user_ids

        if created_with:
            headers["created_with"] = created_with
        if description:
            headers["description"] = description
        if duration:
            headers["duration"] = duration
        if project_id:
            headers["project_id"] = project_id
        if start:
            headers["start"] = start
        elif start_date:
            headers["start_date"] = start_date
        if stop:
            headers["stop"] = stop
        if tag_action:
            headers["tag_action"] = tag_action
        if tag_ids:
            headers["tag_ids"] = tag_ids
        if tags:
            headers["tags"] = tags

        return headers

    def edit_tracker(self, tracker_id: int, **kwargs) -> TogglTracker | None:
        data = self.request(
            f"/{tracker_id}",
            method=RequestMethod.PUT,
            body=self.body_creation(**kwargs),
        )
        if data is None:
            return None

        return self.model.from_kwargs(**data)

    def delete_tracker(self, tracker_id: int) -> None:
        self.request(f"/{tracker_id}", method=RequestMethod.DELETE)

    def stop_tracker(self, tracker_id: int) -> TogglTracker | None:
        data = self.request(f"/{tracker_id}/stop", method=RequestMethod.PATCH)
        if data is None:
            return None

        return self.model.from_kwargs(**data)

    def add_tracker(self, **kwargs) -> TogglTracker | None:
        data = self.request(
            "",
            method=RequestMethod.POST,
            body=self.body_creation(**kwargs),
        )
        if data is None:
            return None
        return self.model.from_kwargs(**data)

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/time_entries"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker


class TrackerCachedEndpoint(TogglCachedEndpoint):
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

        params = ""
        if since and before:
            params = f"?since={since}&before={before}"
        elif start_date and end_date:
            params = f"?start_date={start_date}&end_date={end_date}"
        response = self.request(params, refresh=refresh)

        if not isinstance(response, list):
            return None

        return self.process_models(response)

    def get_tracker(
        self,
        tracker_id: int,
        *,
        refresh: bool = False,
    ) -> TogglTracker | None:
        cache = self.load_cache() if not refresh else None
        if isinstance(cache, list):
            entries = self.process_models(cache)
            for item in entries:
                if item.id == tracker_id:
                    return self.model.from_kwargs(**item)  # type: ignore[return-value]

        try:
            response = self.request(f"/{tracker_id}", refresh=refresh)
        except HTTPError:
            response = None

        if not isinstance(response, dict):
            return None

        return self.model.from_kwargs(**response)

    @property
    def endpoint(self) -> str:
        return super().endpoint + "me/time_entries"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
