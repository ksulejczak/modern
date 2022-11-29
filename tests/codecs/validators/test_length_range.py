from collections.abc import Sized

import pytest

from modern.codecs.validators.length_range import LengthRange


@pytest.mark.parametrize(
    "value",
    [
        "",
        "123" "123456",
        [],
        [1, 2, 3],
        [1, 2, 3, 4, 5, 6],
        (1, 2, 3, 4, 5, 6),
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6},
    ],
)
def test_max_length_false(value: Sized) -> None:
    validator = LengthRange(4, 5)

    assert validator(value) is False


@pytest.mark.parametrize(
    "value",
    [
        "1234",
        "12345",
        [1, 2, 3, 4],
        [1, 2, 3, 4, 5],
        (1, 2, 3, 4, 5),
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
    ],
)
def test_max_length_true(value: Sized) -> None:
    validator = LengthRange(4, 5)

    assert validator(value) is True


def test_infinitive_length() -> None:
    validator = LengthRange(4, None)

    assert validator(bytes(0x1000)) is True


def test_repr() -> None:
    validator = LengthRange(4, 5)

    assert repr(validator) == "<LengthRange gte=4 lte=5>"
