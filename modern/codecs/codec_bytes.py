from .base import Codec


class BytesCodec(Codec[bytes]):
    name = "bytes"

    def in_(self, data: bytes) -> bytes:
        return data

    def out(self, value: bytes) -> bytes:
        return value
