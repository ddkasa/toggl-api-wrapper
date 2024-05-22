from datetime import datetime


def get_workspace(data: dict) -> int:
    workspace = data.get("workspace_id")
    if workspace:
        return workspace
    return data["wid"]


# NOTE: Date utilities for python 3.10 compatibility.
def format_iso(date: datetime) -> str:
    return date.isoformat(timespec="seconds")


def parse_iso(date: str) -> datetime:
    if date.endswith("Z"):
        date = date[:-1] + "-00:00"
    return datetime.fromisoformat(date)
