from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

F = TypeVar("F")
T = TypeVar("T")


class CodecError(Exception):
    pass


class Codec(Generic[F, T], ABC):
    @abstractmethod
    def __call__(self, data: F) -> T:  # pragma: no cover
        ...

    def __or__(self, right: Codec[F, T]) -> OrCodec[F, T]:
        return OrCodec(self, right)


OF = TypeVar("OF")
OT = TypeVar("OT")


class OrCodec(Codec[OF, OT]):
    name = "__or__"

    def __init__(self, left: Codec[OF, OT], right: Codec[OF, OT]) -> None:
        self._left = left
        self._right = right

    def __call__(self, data: OF) -> OT:
        for op in (self._left, self._right):
            try:
                return op(data)
            except CodecError:
                pass
        else:
            raise CodecError(data)


NT = TypeVar("NT")


class NoopCodec(Codec[NT, NT]):
    def __call__(self, data: NT) -> NT:
        return data


CF = TypeVar("CF")
CT = TypeVar("CT")
CI = TypeVar("CI")


class CombinedCodec(Codec[CF, CT], Generic[CF, CI, CT]):
    def __init__(
        self,
        first: Codec[CF, CI],
        second: Codec[CI, CT],
    ) -> None:
        self._first = first
        self._second = second

    def __call__(self, data: CF) -> CT:
        return self._second(self._first(data))
