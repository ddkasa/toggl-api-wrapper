from datetime import datetime, timedelta, timezone
from typing import Optional

from httpx import HTTPStatusError

from toggl_api.utility import format_iso

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTracker


class TrackerEndpoint(TogglCachedEndpoint):
    def body_creation(self, **kwargs) -> dict:  # noqa: C901
        headers = {}
        workspace_id = kwargs.get("workspace_id", self.workspace_id)
        headers["workspace_id"] = workspace_id

        created_with = kwargs.get("created_with", "toggl-api-wrapper")
        description = kwargs.get("description")
        duration = kwargs.get("duration", -1)
        project_id = kwargs.get("project_id")
        start = kwargs.get("start", datetime.now(tz=timezone.utc))
        start_date = kwargs.get("start_date")
        stop = kwargs.get("stop")
        tag_action = kwargs.get("tag_action")
        tag_ids = kwargs.get("tag_ids")
        tags = kwargs.get("tags")
        shared_with_user_ids = kwargs.get("shared_with_user_ids", [])

        headers["shared_with_user_ids"] = shared_with_user_ids

        if created_with:
            headers["created_with"] = created_with
        if not description:
            description = kwargs.get("name")
        if description:
            headers["description"] = description
        if duration:
            headers["duration"] = duration.total_seconds() if isinstance(duration, timedelta) else duration
        if project_id:
            headers["project_id"] = project_id
        if start:
            headers["start"] = format_iso(start)
        elif start_date:
            headers["start_date"] = format_iso(start_date)
        if stop:
            headers["stop"] = format_iso(stop)
        if tag_action:
            headers["tag_action"] = tag_action
        if tag_ids:
            headers["tag_ids"] = tag_ids
        if tags:
            headers["tags"] = tags

        return headers

    def edit_tracker(
        self,
        tracker: TogglTracker,
        **kwargs,
    ) -> Optional[TogglTracker]:
        data = self.request(
            f"/{tracker.id}",
            method=RequestMethod.PUT,
            body=self.body_creation(**kwargs),
            refresh=True,
        )
        if not isinstance(data, self.model):
            return None

        return data

    def delete_tracker(self, tracker: TogglTracker) -> None:
        try:
            self.request(
                f"/{tracker.id}",
                method=RequestMethod.DELETE,
                refresh=True,
            )
        except HTTPStatusError as err:
            if err.response.status_code != self.NOT_FOUND:
                raise
        self.cache.delete_entries(tracker)
        self.cache.commit()

    def stop_tracker(self, tracker: TogglTracker) -> Optional[TogglTracker]:
        return self.request(
            f"/{tracker.id}/stop",
            method=RequestMethod.PATCH,
            refresh=True,
        )  # type: ignore[return-value]

    def add_tracker(self, **kwargs) -> Optional[TogglTracker]:
        return self.request(
            "",
            method=RequestMethod.POST,
            body=self.body_creation(**kwargs),
            refresh=True,
        )  # type: ignore[return-value]

    @property
    def endpoint(self) -> str:
        return super().endpoint + f"workspaces/{self.workspace_id}/time_entries"

    @property
    def model(self) -> type[TogglTracker]:
        return TogglTracker
