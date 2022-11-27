import pytest

from modern.codecs import CodecError
from modern.codecs.codec_bytes_str import BytesToStrCodec, StrToBytesCodec


def test_bytes_to_str() -> None:
    codec = BytesToStrCodec()
    value = b"bytes-value"

    out_value = codec(value)

    assert type(out_value) is str
    assert out_value == "bytes-value"


def test_bytes_to_str_raises_on_invalid_bytes_sequence() -> None:
    codec = BytesToStrCodec()
    value = b"invalid-bytes-value: \233\234"

    with pytest.raises(CodecError):
        codec(value)


def test_str_to_bytes() -> None:
    codec = StrToBytesCodec()
    value = "str-value"

    out_value = codec(value)

    assert type(out_value) is bytes
    assert out_value == b"str-value"


def test_str_to_bytes_raises_on_unencodable_string() -> None:
    codec = StrToBytesCodec("ascii")
    value = "str-value-łó"

    with pytest.raises(CodecError):
        codec(value)
