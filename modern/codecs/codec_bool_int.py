from .base import Codec


class BoolToIntCodec(Codec[bool, int]):
    def __call__(self, data: bool) -> int:
        return int(data)
