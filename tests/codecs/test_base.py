import pytest

from modern.codecs.base import Codec, CodecError


def test_in_raises() -> None:
    codec: Codec[int] = Codec()

    with pytest.raises(NotImplementedError):
        codec.in_(b"")


def test_out_raises() -> None:
    codec: Codec[int] = Codec()

    with pytest.raises(NotImplementedError):
        codec.out(1)


def test_or_codec_in_returns_left() -> None:
    value = b"test text"
    codec: Codec[str] = STR_CODEC | STR_FAILING_CODEC

    in_value = codec.in_(value)

    assert in_value == "test text"


def test_or_codec_in_returns_right() -> None:
    value = b"test text"
    codec: Codec[str] = STR_FAILING_CODEC | STR_CODEC

    in_value = codec.in_(value)

    assert in_value == "test text"


def test_or_codec_raises_if_both_sides_fail() -> None:
    value = b"test text"
    codec: Codec[str] = STR_FAILING_CODEC | STR_FAILING_CODEC

    with pytest.raises(CodecError):
        codec.in_(value)


def test_or_codec_out_value_from_left_side() -> None:
    value = "test text"
    codec: Codec[str] = STR_CODEC | STR_FAILING_CODEC

    out_value = codec.out(value)

    assert out_value == b"test text"


class StrTestCodec(Codec[str]):
    def in_(self, data: bytes) -> str:
        return data.decode()

    def out(self, value: str) -> bytes:
        return value.encode()


class FailingStrTestCodec(Codec[str]):
    def in_(self, data: bytes) -> str:
        raise CodecError(data)

    def out(self, value: str) -> bytes:
        return value.encode() + b"SENTINEL"


STR_CODEC = StrTestCodec()
STR_FAILING_CODEC = FailingStrTestCodec()
