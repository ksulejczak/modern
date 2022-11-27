import pytest

from modern.codecs import CodecError
from modern.codecs.codec_bool_str import BoolToStrCodec

BOOL_TO_STR = BoolToStrCodec(true_value="TRUE", false_value="FALSE")


def test_returns_true() -> None:
    out_value = BOOL_TO_STR(True)

    assert type(out_value) is str
    assert out_value == "TRUE"


def test_returns_false() -> None:
    out_value = BOOL_TO_STR(False)

    assert type(out_value) is str
    assert out_value == "FALSE"


def test_raises_on_not_bool() -> None:
    with pytest.raises(CodecError):
        BOOL_TO_STR(None)  # type: ignore[arg-type]
