import pytest

from modern.codecs import Codec, CodecError
from modern.codecs.codec_str import StrCodec


def test_in() -> None:
    codec: Codec[str] = StrCodec()
    value = b"bytes-value"

    in_value = codec.in_(value)

    assert type(in_value) is str
    assert in_value == "bytes-value"


def test_in_raises_on_invalid_bytes_sequence() -> None:
    codec: Codec[str] = StrCodec()
    value = b"invalid-bytes-value: \233\234"

    with pytest.raises(CodecError):
        codec.in_(value)


def test_out() -> None:
    codec: Codec[str] = StrCodec()
    value = "str-value"

    out_value = codec.out(value)

    assert type(out_value) is bytes
    assert out_value == b"str-value"
