import re
from typing import Pattern

from .base import Validator


class RegexMatch(Validator):
    def __init__(self, pattern: Pattern | str) -> None:
        self._pattern = (
            pattern if isinstance(pattern, Pattern) else re.compile(pattern)
        )

    def __call__(self, value: str) -> bool:
        return bool(self._pattern.match(value))
