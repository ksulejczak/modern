from .base import Codec, CodecError


class IntCodec(Codec[int]):
    name = "int"

    def in_(self, data: bytes) -> int:
        try:
            return int(data.decode())
        except ValueError as e:
            raise CodecError(data) from e

    def out(self, value: int) -> bytes:
        return str(value).encode()
