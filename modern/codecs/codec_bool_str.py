from .base import Codec, CodecError


class BoolToStrCodec(Codec[bool, str]):
    def __init__(self, true_value: str, false_value: str) -> None:
        self._true_value = true_value
        self._false_value = false_value

    def __call__(self, data: bool) -> str:
        if data is True:
            return self._true_value
        if data is False:
            return self._false_value
        raise CodecError(data)
