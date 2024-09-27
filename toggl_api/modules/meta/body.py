from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class BaseBody(ABC):
    @abstractmethod
    def format(self, workspace_id: int) -> dict[str, Any]:
        pass
