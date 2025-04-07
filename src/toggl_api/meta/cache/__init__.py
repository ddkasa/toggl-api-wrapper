"""Classes for caching requests locally."""

from ._base_cache import Comparison, TogglCache, TogglQuery
from ._json_cache import CustomDecoder, CustomEncoder, JSONCache, JSONSession

__all__ = [
    "Comparison",
    "CustomDecoder",
    "CustomEncoder",
    "JSONCache",
    "JSONSession",
    "TogglCache",
    "TogglQuery",
]
try:
    from ._sqlite_cache import SqliteCache  # NOTE: Appended in final statment.
except ImportError:
    pass
else:
    __all__ += ["SqliteCache"]
