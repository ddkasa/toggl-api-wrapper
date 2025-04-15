"""Public module for all related dataclasses for Toggl and additonal utility."""

from dataclasses import fields
from typing import Any

from ._models import (
    TogglClass,
    TogglClient,
    TogglOrganization,
    TogglProject,
    TogglTag,
    TogglTracker,
    TogglWorkspace,
    WorkspaceChild,
)
from ._schema import register_tables


def as_dict_custom(obj: TogglClass) -> dict[str, Any]:
    """Convert a TogglClass` to a dictionary.

    Args:
        obj: A `ToggClass` instance.

    Returns:
        `TogglClass` converted to a dictionary.
    """
    data: dict[str, Any] = {"class": obj.__tablename__}

    for field in fields(obj):
        field_data = getattr(obj, field.name)

        if isinstance(field_data, TogglClass):
            data[field.name] = as_dict_custom(field_data)
        elif isinstance(field_data, list):
            data[field.name] = [as_dict_custom(item) for item in field_data]
        else:
            data[field.name] = field_data

    return data


__all__ = (
    "TogglClass",
    "TogglClient",
    "TogglOrganization",
    "TogglProject",
    "TogglTag",
    "TogglTracker",
    "TogglWorkspace",
    "WorkspaceChild",
    "as_dict_custom",
    "register_tables",
)
