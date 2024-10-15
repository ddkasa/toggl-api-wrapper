import functools
import importlib.util
from collections.abc import Callable
from datetime import date, datetime, timezone
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def requires(module: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def requires_dec(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if importlib.util.find_spec(module) is None:
                msg = f"'{module.title()}' is required for this functionality!"
                raise ImportError(msg)
            return fn(*args, **kwargs)

        return wrapper

    return requires_dec


def get_workspace(data: dict) -> int:
    workspace = data.get("workspace_id")
    if isinstance(workspace, int):
        return workspace
    workspace = data.get("wid")
    if isinstance(workspace, int):
        return workspace
    workspace = data.get("workspace")
    if isinstance(workspace, int):
        return workspace
    msg = "Workspace not found!"
    raise KeyError(msg)


# NOTE: Date utilities for python 3.10 compatibility.
def format_iso(date_obj: datetime | date | str) -> str:
    if isinstance(date_obj, str):
        return date_obj
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%FT%TZ")
    return date_obj.isoformat()


def parse_iso(date_obj: str | datetime | date) -> datetime | date:
    if isinstance(date_obj, date):
        return date_obj
    if isinstance(date_obj, datetime):
        return date_obj.replace(tzinfo=timezone.utc)
    if date_obj.endswith("Z"):
        date_obj = date_obj[:-1] + "-00:00"
    return datetime.fromisoformat(date_obj).replace(tzinfo=timezone.utc)
