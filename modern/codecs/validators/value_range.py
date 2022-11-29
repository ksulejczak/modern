from typing import Protocol, TypeVar

from .base import Validator

CT = TypeVar("CT", contravariant=True)


class SupportsRichComparison(Protocol[CT]):
    def __gt__(self, other: CT) -> bool:  # pragma: no cover
        ...

    def __ge__(self, other: CT) -> bool:  # pragma: no cover
        ...

    def __lt__(self, other: CT) -> bool:  # pragma: no cover
        ...

    def __le__(self, other: CT) -> bool:  # pragma: no cover
        ...


T = TypeVar("T", bound=SupportsRichComparison)


class ValueRange(Validator):
    def __init__(
        self,
        gt: T | None = None,
        gte: T | None = None,
        lt: T | None = None,
        lte: T | None = None,
    ) -> None:
        self._gt = gt
        self._gte = gte
        self._lt = lt
        self._lte = lte

    def __call__(self, value: T) -> bool:
        if self._gt is not None and value <= self._gt:
            return False
        if self._gte is not None and value < self._gte:
            return False
        if self._lt is not None and value >= self._lt:
            return False
        if self._lte is not None and value > self._lte:
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}"
            f" gt={self._gt}"
            f" gte={self._gte}"
            f" lt={self._lt}"
            f" lte={self._lte}>"
        )
