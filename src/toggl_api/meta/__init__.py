"""Base classes for requesting data from the Toggl API."""

from ._base_endpoint import TogglEndpoint
from ._body import BaseBody
from ._cached_endpoint import TogglCachedEndpoint
from ._enums import RequestMethod

__all__ = (
    "BaseBody",
    "RequestMethod",
    "TogglCachedEndpoint",
    "TogglEndpoint",
)
