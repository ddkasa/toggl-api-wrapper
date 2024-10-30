from __future__ import annotations

from typing import TYPE_CHECKING

from .meta import TogglCachedEndpoint
from .models import TogglOrganization

if TYPE_CHECKING:
    from httpx import BasicAuth

    from toggl_api.meta.cache.base_cache import TogglCache


class OrganizationEndpoint(TogglCachedEndpoint):
    """Endpoint to do with handling organization specific details.

    [Official Documentation](https://engineering.toggl.com/docs/api/organizations)
    """

    def __init__(self, auth: BasicAuth, cache: TogglCache, *, timeout: int = 20, **kwargs) -> None:
        super().__init__(0, auth, cache, timeout=timeout, **kwargs)

    @property
    def model(self) -> type[TogglOrganization]:
        return TogglOrganization

    @property
    def endpoint(self) -> str:
        return ""
