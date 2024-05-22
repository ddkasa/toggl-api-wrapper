import json
from abc import abstractmethod
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

from toggl_api.version import version

from .meta import RequestMethod, TogglEndpoint


class TogglCachedEndpoint(TogglEndpoint):
    # TODO: Use a simple sqlite DB for cache.
    # TODO: Caching method should really store a table for each object instead of a request.
    __slots__ = ("_cache_path", "_expire_after")

    def __init__(  # noqa: PLR0913
        self,
        cache_path: Path,
        workspace_id: int,
        auth: httpx.BasicAuth,
        expire_after: timedelta = timedelta(days=1),
        *,
        timeout: int = 20,
        **kwargs,
    ) -> None:
        super().__init__(
            workspace_id=workspace_id,
            auth=auth,
            timeout=timeout,
            **kwargs,
        )
        cache_path.mkdir(parents=True, exist_ok=True)
        self._cache_path = cache_path
        self._expire_after = expire_after

    def request(  # type: ignore[override]
        self,
        parameters: str,
        headers: Optional[dict] = None,
        method: RequestMethod = RequestMethod.GET,
        *,
        refresh: bool = False,
    ) -> httpx.Response:
        if not refresh and method == RequestMethod.GET:
            data = self.load_cache()
            if data:
                return data

        response = super().request(
            parameters,
            method=method,
            headers=headers,
        )

        if self.expire_after.total_seconds() > 0 and isinstance(response, dict):
            self.save_cache(response)

        return response

    def load_cache(self) -> None | dict:
        now = datetime.now(tz=UTC)
        if not self.cache_path.exists():
            return None
        with self.cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if now - self.expire_after <= datetime.fromisoformat(data["timestamp"]):
            return data["data"]

        return None

    def save_cache(self, data: dict) -> None:
        data = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "data": data,
            "version": version,
        }
        with self.cache_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def process_models(self, data: list[dict]) -> list:
        return [self.model.from_kwargs(**tracker) for tracker in data]

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        # REFACTOR: Might be better to return a folder instead of file and decide cache by method.
        return self._cache_path

    @property
    def expire_after(self) -> timedelta:
        return self._expire_after

    @expire_after.setter
    def expire_after(self, value: timedelta) -> None:
        self._expire_after = value

    @property
    @abstractmethod
    def endpoint(self) -> str:
        return super().endpoint
