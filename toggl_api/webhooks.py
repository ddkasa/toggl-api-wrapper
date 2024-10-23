from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import cache
from typing import Any, Optional

import httpx
from httpx import HTTPStatusError

from toggl_api.meta.body import BaseBody
from toggl_api.meta.cached_endpoint import TogglCachedEndpoint
from toggl_api.meta.enums import RequestMethod
from toggl_api.models.models import TogglSubscription

log = logging.getLogger("toggl-api-wrapper.endpoint")


@dataclass
class WebhookBody(BaseBody):
    callback_url: str = field(default="")
    description: str = field(default="")
    secret: Optional[str] = field(default=None)
    enabled: bool = field(default=True)
    event_filters: list[str] = field(default_factory=list)
    has_pending_events: bool = field(default=False)

    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        body["description"] = self.description
        body["enabled"] = self.enabled
        body["event_filters"] = self.event_filters
        body["has_pending_events"] = self.has_pending_events
        body["secret"] = self.secret

        return body


class WebhookEndpoint(TogglCachedEndpoint):
    BASE_ENDPOINT = "https://api.track.toggl.com/webhooks/api/v1/"

    @classmethod
    @cache
    def get_event_filters(cls) -> dict[str, list[str]]:
        return httpx.get(cls.BASE_ENDPOINT + "event_filters").json()

    @classmethod
    def api_status(cls) -> bool:
        try:
            response = httpx.get(cls.BASE_ENDPOINT + "status").json()
        except HTTPStatusError:
            log.critical("Failed to get a response from the Toggl webhooks API!")
            log.exception("%s")
            return False

        return bool(response) and response.get("status") == "OK"

    @property
    def model(self) -> type[TogglSubscription]:
        return TogglSubscription


class SubscriptionEndpoint(WebhookEndpoint):
    def collect(self, *, refresh: bool = False) -> list[TogglSubscription]:
        return self.request("", refresh=refresh)

    def add(self, body: WebhookBody) -> TogglSubscription | None:
        response = self.request(
            "",
            body=body.format("add", workspace_id=self.workspace_id),
            refresh=True,
            method=RequestMethod.POST,
        )

        return response[0] if response else None

    def edit(self, webhook: TogglSubscription | int, body: WebhookBody) -> TogglSubscription:
        return self.request(
            f"/{int(webhook)}",
            body=body.format("edit", workspace_id=self.workspace_id),
            method=RequestMethod.PUT,
            refresh=True,
        )

    def delete(self, webhook: TogglSubscription | int) -> TogglSubscription:
        return self.request(
            f"/{int(webhook)}",
            method=RequestMethod.DELETE,
            refresh=True,
        )

    def toggle(self, webhook: TogglSubscription | int, *, status: bool) -> TogglSubscription:
        return self.request(
            f"/{int(webhook)}",
            body={"enabled": status},
            method=RequestMethod.PATCH,
            refresh=True,
        )

    @property
    def endpoint(self) -> str:
        return self.BASE_ENDPOINT + f"subscriptions/{self.workspace_id}"

    @property
    def model(self) -> type[TogglSubscription]:
        return TogglSubscription
