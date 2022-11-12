import pytest

from modern.codecs.codec_bool_int import BoolToIntCodec

BOOL_TO_INT = BoolToIntCodec()


@pytest.mark.parametrize(
    ["in_value", "expected"],
    [
        (False, 0),
        (True, 1),
    ],
)
def test_converts_bool_to_int(in_value: bool, expected: int) -> None:
    out_value = BOOL_TO_INT(in_value)

    assert type(out_value) is int
    assert out_value == expected
