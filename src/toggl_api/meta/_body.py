from abc import abstractmethod
from collections.abc import Iterator, Mapping
from dataclasses import MISSING, dataclass
from typing import Any


@dataclass
class BaseBody(Mapping[str, Any]):
    @abstractmethod
    def format(self, endpoint: str, **body: Any) -> dict[str, Any]:
        pass

    @classmethod
    def _verify_endpoint_parameter(cls, parameter: str, endpoint: str) -> bool:
        """Check if a body parameter is valid for a specified endpoint.

        Args:
            parameter: Name of the attribute to check.
            endpoint: The endpoint to check for.

        Raises:
            KeyError: If the parameter is not present in the dataclass.

        Returns:
            True if the parameter is valid for the endpoint.
        """
        field = cls.__dataclass_fields__.get(parameter)
        if field is None:
            msg = "Validating a non-existant field!"
            raise KeyError(msg)
        endpoints = field.metadata.get("endpoints", frozenset())
        return not endpoints or endpoint in endpoints

    def __iter__(self) -> Iterator[Any]:
        yield from self.format("")

    def __delitem__(self, key: str, /) -> None:
        field = self.__dataclass_fields__[key]
        if field.default is not MISSING:
            setattr(self, key, field.default)
        elif field.default_factory is not MISSING:
            setattr(self, key, field.default_factory())

    def __getitem__(self, key: str, /) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any, /) -> None:
        return setattr(self, key, value)

    def __len__(self) -> int:
        return len(self.format(""))
