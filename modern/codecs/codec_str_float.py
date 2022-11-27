from .base import Codec, CodecError


class StrToFloatCodec(Codec[str, float]):
    def __call__(self, data: str) -> float:
        try:
            return float(data)
        except ValueError as e:
            raise CodecError(data) from e


class FloatToStrCodec(Codec[float, str]):
    def __call__(self, value: float) -> str:
        return str(value)
