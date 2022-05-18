from .base import Codec, CodecError


class StrCodec(Codec[str]):
    name = "str"

    def in_(self, data: bytes) -> str:
        try:
            return data.decode()
        except UnicodeDecodeError as e:
            raise CodecError(data) from e

    def out(self, value: str) -> bytes:
        return value.encode()
