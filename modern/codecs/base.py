from __future__ import annotations

from typing import ClassVar, Generic, TypeVar

T = TypeVar("T")


class CodecError(Exception):
    pass


class Codec(Generic[T]):
    name: ClassVar[str]

    def in_(self, data: bytes) -> T:
        raise NotImplementedError(self)

    def out(self, value: T) -> bytes:
        raise NotImplementedError(self)

    def __or__(self, right: Codec[T]) -> OrCodec[T]:
        return OrCodec(self, right)


OT = TypeVar("OT")


class OrCodec(Codec[OT]):
    name = "__or__"

    def __init__(self, left: Codec[OT], right: Codec[OT]) -> None:
        self._left = left
        self._right = right

    def in_(self, data: bytes) -> OT:
        for op in (self._left, self._right):
            try:
                return op.in_(data)
            except CodecError:
                pass
        else:
            raise CodecError(data)

    def out(self, value: OT) -> bytes:
        return self._left.out(value)
