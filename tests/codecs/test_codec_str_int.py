import pytest

from modern.codecs import CodecError
from modern.codecs.codec_str_int import IntToStrCodec, StrToIntCodec


def test_str_to_int() -> None:
    codec = StrToIntCodec()
    value = "1234"

    out_value = codec(value)

    assert type(out_value) is int
    assert out_value == 1234


def test_in_raises_not_recognized_int() -> None:
    codec = StrToIntCodec()
    value = "123.5"

    with pytest.raises(CodecError):
        codec(value)


def test_out() -> None:
    codec = IntToStrCodec()
    value = 1234

    out_value = codec(value)

    assert type(out_value) is str
    assert out_value == "1234"
