import pytest

from modern.codecs import CodecError
from modern.codecs.codec_str_float import FloatToStrCodec, StrToFloatCodec


def test_str_to_float() -> None:
    codec = StrToFloatCodec()
    value = "1234.987"

    in_value = codec(value)

    assert type(in_value) is float
    assert in_value == 1234.987


def test_str_to_float_raises_on_not_recognized_float_string() -> None:
    codec = StrToFloatCodec()
    value = "123.5.2"

    with pytest.raises(CodecError):
        codec(value)


def test_float_to_str() -> None:
    codec = FloatToStrCodec()
    value = 1234.987

    out_value = codec(value)

    assert type(out_value) is str
    assert out_value == "1234.987"
