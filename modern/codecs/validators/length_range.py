from collections.abc import Sized

from .base import Validator


class LengthRange(Validator):
    def __init__(self, gte: int, lte: int | None) -> None:
        self._gte = gte
        self._lte = lte

    def __call__(self, value: Sized) -> bool:
        length = len(value)
        return length >= self._gte and (
            self._lte is None or length <= self._lte
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} gte={self._gte} lte={self._lte}>"
