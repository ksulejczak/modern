from .base import Codec, CodecError


class FloatToIntCodec(Codec[float, int]):
    def __call__(self, data: float) -> int:
        try:
            int_value = int(data)
        except (OverflowError, ValueError) as e:
            raise CodecError(data) from e
        if float(int_value) != data:
            raise CodecError(data)
        return int_value


class FloatToIntRoundCodec(Codec[float, int]):
    def __call__(self, data: float) -> int:
        try:
            return round(data)
        except (OverflowError, ValueError) as e:
            raise CodecError(data) from e


class IntToFloatCodec(Codec[int, float]):
    def __call__(self, data: int) -> float:
        return float(data)
