import pytest

from modern.codecs import Codec, CodecError
from modern.codecs.codec_float import FloatCodec


def test_in() -> None:
    codec: Codec[float] = FloatCodec()
    value = b"1234.987"

    in_value = codec.in_(value)

    assert type(in_value) is float
    assert in_value == 1234.987


def test_in_raises_not_recognized_float() -> None:
    codec: Codec[float] = FloatCodec()
    value = b"123.5.2"

    with pytest.raises(CodecError):
        codec.in_(value)


def test_out() -> None:
    codec: Codec[float] = FloatCodec()
    value = 1234.987

    out_value = codec.out(value)

    assert type(out_value) is bytes
    assert out_value == b"1234.987"
