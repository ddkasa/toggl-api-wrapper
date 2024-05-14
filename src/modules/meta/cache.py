import json
from abc import abstractmethod
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from version import __version__

from .meta import RequestMethod, TogglRequest


class CacheTogglRequest(TogglRequest):
    __slots__ = ("__expire_after",)

    def __init__(
        self,
        expire_after: timedelta,
        *,
        timeout: int = 20,
        **kwargs,
    ) -> None:
        super().__init__(timeout=timeout, **kwargs)
        self.__expire_after = expire_after

    def request(
        self,
        parameters: str,
        method: RequestMethod = RequestMethod.GET,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> httpx.Response:
        if not refresh:
            data = self.load_cache()
            if data:
                return data

        response = super().request(parameters, request_method=method, **kwargs)

        if self.expire_after.total_seconds() > 0:
            self.save_cache(response)

        return response

    def load_cache(self) -> None | dict:
        now = datetime.now(tz=UTC)

        with self.cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

            if now - self.expire_after <= datetime.fromisoformat(data["time_stamp"]):
                return data["data"]

        return None

    def save_cache(self, data: dict) -> None:
        now = datetime.now(tz=UTC)
        data = {
            "timestamp": now.isoformat(),
            "data": data,
            "version": __version__,
        }
        with self.cache_path.open("w", encoding="utf-8") as f:
            json.dump(json, f)

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        pass

    @property
    def expire_after(self) -> timedelta:
        return self.__expire_after

    @property
    @abstractmethod
    def endpoint(self) -> str:
        return super().endpoint
