import pytest

from modern.codecs import CodecError
from modern.codecs.codec_float_int import (
    FloatToIntCodec,
    FloatToIntRoundCodec,
    IntToFloatCodec,
)


def test_float_to_int() -> None:
    codec = FloatToIntCodec()
    value = 123.0

    out_value = codec(value)

    assert type(out_value) is int
    assert out_value == 123


@pytest.mark.parametrize(
    "value", [float("inf"), float("-inf"), float("nan"), 123.1]
)
def test_float_to_int_raises_on_invalid_value(value: float) -> None:
    codec = FloatToIntCodec()

    with pytest.raises(CodecError):
        codec(value)


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        (123.0, 123),
        (123.4, 123),
        (123.6, 124),
        (-123.4, -123),
        (-123.6, -124),
    ],
)
def test_float_to_int_round(value: float, expected: int) -> None:
    codec = FloatToIntRoundCodec()

    out_value = codec(value)

    assert type(out_value) is int
    assert out_value == expected


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_float_to_int_rounded_raises_on_invalid_value(value: float) -> None:
    codec = FloatToIntRoundCodec()

    with pytest.raises(CodecError):
        codec(value)


def test_int_to_float() -> None:
    codec = IntToFloatCodec()
    value = 123

    out_value = codec(value)

    assert type(out_value) is float
    assert out_value == 123.0
