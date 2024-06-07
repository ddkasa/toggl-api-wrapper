from datetime import datetime, timezone


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
def format_iso(date: datetime) -> str:
    return date.isoformat(timespec="seconds")


def parse_iso(date: str | datetime) -> datetime:
    if isinstance(date, datetime):
        return date.replace(tzinfo=timezone.utc)
    if date.endswith("Z"):
        date = date[:-1] + "-00:00"
    return datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
