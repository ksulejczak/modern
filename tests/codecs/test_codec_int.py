import pytest

from modern.codecs import Codec, CodecError
from modern.codecs.codec_int import IntCodec


def test_in() -> None:
    codec: Codec[int] = IntCodec()
    value = b"1234"

    in_value = codec.in_(value)

    assert type(in_value) is int
    assert in_value == 1234


def test_in_raises_not_recognized_int() -> None:
    codec: Codec[int] = IntCodec()
    value = b"123.5"

    with pytest.raises(CodecError):
        codec.in_(value)


def test_out() -> None:
    codec: Codec[int] = IntCodec()
    value = 1234

    out_value = codec.out(value)

    assert type(out_value) is bytes
    assert out_value == b"1234"
