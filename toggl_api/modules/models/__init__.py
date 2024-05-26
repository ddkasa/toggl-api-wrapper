from dataclasses import fields
from typing import Any

from .models import TogglClass, TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace
from .schema import register_tables


def as_dict_custom(obj: TogglClass) -> dict[str, Any]:
    data = {"class": obj.__tablename__}

    for field in fields(obj):
        field_data = getattr(obj, field.name)

        if isinstance(field_data, TogglClass):
            data[field.name] = as_dict_custom(field_data)
        elif isinstance(field_data, list):
            data[field.name] = [as_dict_custom(item) for item in field_data]
        else:
            data[field.name] = field_data

    print(data)
    return data


__all__ = (
    "TogglTag",
    "TogglClient",
    "TogglProject",
    "TogglClass",
    "TogglTracker",
    "TogglWorkspace",
    "register_tables",
    "as_dict_custom",
)
