from modern.codecs import Codec
from modern.codecs.codec_bytes import BytesCodec


def test_in() -> None:
    codec: Codec[bytes] = BytesCodec()
    value = b"bytes-value"

    in_value = codec.in_(value)

    assert in_value is value


def test_out() -> None:
    codec: Codec[bytes] = BytesCodec()
    value = b"bytes-value"

    out_value = codec.out(value)

    assert out_value is value
