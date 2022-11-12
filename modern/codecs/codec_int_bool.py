from .base import Codec, CodecError


class IntToBoolCodec(Codec[int, bool]):
    def __call__(self, data: int) -> bool:
        if data == 1:
            return True
        if data == 0:
            return False
        raise CodecError(data)
