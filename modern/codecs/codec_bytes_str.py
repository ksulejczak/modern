from .base import Codec, CodecError


class BytesToStrCodec(Codec[bytes, str]):
    def __init__(self, encoding: str = "utf-8"):
        self._encoding = encoding

    def __call__(self, data: bytes) -> str:
        try:
            return data.decode(self._encoding, errors="strict")
        except UnicodeDecodeError as e:
            raise CodecError(data) from e


class StrToBytesCodec(Codec[str, bytes]):
    def __init__(self, encoding: str = "utf-8"):
        self._encoding = encoding

    def __call__(self, data: str) -> bytes:
        try:
            return data.encode(self._encoding, errors="strict")
        except UnicodeEncodeError as e:
            raise CodecError(data) from e
