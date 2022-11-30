from abc import ABC, abstractmethod
from typing import Any


class Validator(ABC):
    @abstractmethod
    def __call__(self, value: Any) -> bool:  # pragma: no cover
        ...
