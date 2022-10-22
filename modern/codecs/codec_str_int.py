from .base import Codec, CodecError


class StrToIntCodec(Codec[str, int]):
    def __call__(self, data: str) -> int:
        try:
            return int(data)
        except ValueError as e:
            raise CodecError(data) from e


class IntToStrCodec(Codec[int, str]):
    def __call__(self, data: int) -> str:
        return str(data)
