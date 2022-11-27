from collections.abc import Iterable

from .base import Codec, CodecError


class StrToBoolCodec(Codec[str, bool]):
    def __init__(
        self, true_values: Iterable[str], false_values: Iterable[str]
    ) -> None:
        self._true_values = frozenset(map(str.lower, true_values))
        self._false_values = frozenset(map(str.lower, false_values))

    def __call__(self, data: str) -> bool:
        data = data.lower()
        if data in self._true_values:
            return True
        if data in self._false_values:
            return False
        raise CodecError(data)
