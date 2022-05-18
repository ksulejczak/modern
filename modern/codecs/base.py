from typing import ClassVar, Generic, TypeVar

T = TypeVar("T")


class Codec(Generic[T]):
    name: ClassVar[str]

    def in_(self, data: bytes) -> T:
        raise NotImplementedError(self)

    def out(self, value: T) -> bytes:
        raise NotImplementedError(self)
