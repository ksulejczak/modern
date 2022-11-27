import pytest

from modern.codecs import CodecError
from modern.codecs.codec_int_bool import IntToBoolCodec

INT_TO_BOOL = IntToBoolCodec()


def test_returns_true() -> None:
    out_value = INT_TO_BOOL(1)

    assert out_value is True


def test_returns_false() -> None:
    out_value = INT_TO_BOOL(0)

    assert out_value is False


@pytest.mark.parametrize("value", [-2, -1, 2, 3, 4])
def test_raises_on_unknown_value(value: int) -> None:
    with pytest.raises(CodecError):
        INT_TO_BOOL(value)
