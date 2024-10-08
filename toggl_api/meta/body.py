from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class BaseBody(ABC):
    @abstractmethod
    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        pass

    @classmethod
    def verify_endpoint_parameter(cls, parameter: str, endpoint: str) -> bool:
        """Checks if a body parameter is valid for a specified endpoint."""
        field = cls.__dataclass_fields__.get(parameter)
        if field is None:
            msg = "Validating a non-existant field!"
            raise ValueError(msg)
        endpoints = field.metadata.get("endpoints", frozenset())
        return not field or endpoint in endpoints
