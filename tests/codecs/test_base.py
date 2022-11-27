import pytest

from modern.codecs.base import Codec, CodecError, CombinedCodec, NoopCodec


def test_or_codec_in_returns_left() -> None:
    value = b"test text"
    codec = STR_CODEC | STR_FAILING_CODEC

    in_value = codec(value)

    assert in_value == "test text"


def test_or_codec_in_returns_right() -> None:
    value = b"test text"
    codec = STR_FAILING_CODEC | STR_CODEC

    in_value = codec(value)

    assert in_value == "test text"


def test_or_codec_raises_if_both_sides_fail() -> None:
    value = b"test text"
    codec = STR_FAILING_CODEC | STR_FAILING_CODEC

    with pytest.raises(CodecError):
        codec(value)


def test_noop_codec_in() -> None:
    value = "a b c"

    in_value = STR_NOOP_CODEC(value)

    assert in_value is value


def test_combined_codec_in() -> None:
    value = b"123"

    in_value = BYTES_TO_INT_COMBINED_CODEC(value)

    assert in_value == 123


class StrTestCodec(Codec[bytes, str]):
    def __call__(self, data: bytes) -> str:
        return data.decode()


class IntTestCodec(Codec[str, int]):
    def __call__(self, data: str) -> int:
        return int(data)


class FailingStrTestCodec(Codec[bytes, str]):
    def __call__(self, data: bytes) -> str:
        raise CodecError(data)


class StrNoopCodec(NoopCodec[str]):
    pass


class BytesToIntCombinedCodec(CombinedCodec[bytes, str, int]):
    pass


STR_CODEC = StrTestCodec()
STR_FAILING_CODEC = FailingStrTestCodec()
STR_NOOP_CODEC = StrNoopCodec()
BYTES_TO_INT_COMBINED_CODEC = BytesToIntCombinedCodec(
    first=StrTestCodec(),
    second=IntTestCodec(),
)
