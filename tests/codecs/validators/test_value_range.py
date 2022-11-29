import pytest

from modern.codecs.validators.value_range import ValueRange


@pytest.mark.parametrize("value", [0, 2, 4, 5])
def test_gt_false(value: int) -> None:
    validator = ValueRange(gt=5)

    assert validator(value) is False


@pytest.mark.parametrize("value", [6, 7, 8])
def test_gt_true(value: int) -> None:
    validator = ValueRange(gt=5)

    assert validator(value) is True


@pytest.mark.parametrize("value", [0, 2, 4])
def test_gte_false(value: int) -> None:
    validator = ValueRange(gte=5)

    assert validator(value) is False


@pytest.mark.parametrize("value", [5, 6, 7, 8])
def test_gte_true(value: int) -> None:
    validator = ValueRange(gte=5)

    assert validator(value) is True


@pytest.mark.parametrize("value", [5, 6, 7, 8])
def test_lt_false(value: int) -> None:
    validator = ValueRange(lt=5)

    assert validator(value) is False


@pytest.mark.parametrize("value", [0, 2, 4])
def test_lt_true(value: int) -> None:
    validator = ValueRange(lt=5)

    assert validator(value) is True


@pytest.mark.parametrize("value", [6, 7, 8])
def test_lte_false(value: int) -> None:
    validator = ValueRange(lte=5)

    assert validator(value) is False


@pytest.mark.parametrize("value", [0, 2, 4, 5])
def test_lte_true(value: int) -> None:
    validator = ValueRange(lte=5)

    assert validator(value) is True


def test_repr() -> None:
    validator = ValueRange(gt=1, gte=2, lt=3, lte=4)

    assert repr(validator) == "<ValueRange gt=1 gte=2 lt=3 lte=4>"
