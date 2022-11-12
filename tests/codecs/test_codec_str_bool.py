import pytest

from modern.codecs import CodecError
from modern.codecs.codec_str_bool import StrToBoolCodec

STR_TO_BOOL = StrToBoolCodec(
    true_values=["TRUE", "ON"],
    false_values=["FALSE", "OFF"],
)


@pytest.mark.parametrize("value", ["true", "True", "TRUE", "on", "oN"])
def test_returns_true(value: str) -> None:
    out_value = STR_TO_BOOL(value)

    assert out_value is True


@pytest.mark.parametrize("value", ["false", "False", "FALSE", "off", "oFf"])
def test_returns_false(value: str) -> None:
    out_value = STR_TO_BOOL(value)

    assert out_value is False


def test_raises_on_unknown_value() -> None:
    with pytest.raises(CodecError):
        STR_TO_BOOL("yes")
