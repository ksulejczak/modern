from .base import Codec, CodecError


class FloatCodec(Codec[float]):
    name = "float"

    def in_(self, data: bytes) -> float:
        try:
            return float(data.decode())
        except ValueError as e:
            raise CodecError(data) from e

    def out(self, value: float) -> bytes:
        return str(value).encode()
