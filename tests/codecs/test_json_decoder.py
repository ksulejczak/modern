from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Set, Tuple, Union
from uuid import UUID

import pytest

from modern.codecs import Codec, CodecError
from modern.codecs.json_converter import JsonValue, make_json_decoder


def test_raises_on_unknown_type() -> None:
    class _T:
        pass

    with pytest.raises(TypeError):
        make_json_decoder(_T)


def test_raises_on_invalid_json_value() -> None:
    codec = make_json_decoder(int)

    with pytest.raises(CodecError):
        codec(set())  # type: ignore


def test_raises_on_none_for_not_optional_field() -> None:
    codec = make_json_decoder(int)

    with pytest.raises(CodecError):
        codec(None)


@pytest.mark.parametrize("type_", [list, tuple])
def test_raises_if_container_type_not_annotated(
    type_: type[list] | type[tuple],
) -> None:
    with pytest.raises(TypeError):
        make_json_decoder(type_)


@pytest.mark.parametrize(
    ["type_", "json_value", "expected"],
    [
        (bool, True, True),
        (bool, "true", True),
        (bool, "on", True),
        (bool, "yes", True),
        (bool, "1", True),
        (bool, 1, True),
        (bool, False, False),
        (bool, "false", False),
        (bool, "off", False),
        (bool, "no", False),
        (bool, "0", False),
        (bool, 0, False),
        (int, 123, 123),
        (int, "123", 123),
        (int, 123.0, 123),
        (float, 123, 123.0),
        (float, "123.1", 123.1),
        (float, 123.1, 123.1),
        (str, 123, "123"),
        (str, "123", "123"),
        (str, 123.12, "123.12"),
        (
            datetime,
            1667995689,
            datetime(2022, 11, 9, 12, 8, 9, 0, timezone.utc),
        ),
        (
            datetime,
            "2022-11-09T12:08:09.123456+01:00",
            datetime(2022, 11, 9, 11, 8, 9, 123456, timezone.utc),
        ),
        (
            datetime,
            1667995689.123456,
            datetime(2022, 11, 9, 12, 8, 9, 123456, timezone.utc),
        ),
        (UUID, "01" * 16, UUID("01" * 16)),
    ],
)
def test_converts_single_value(
    type_: type[Any],
    json_value: Any,
    expected: Any,
) -> None:
    codec = make_json_decoder(type_)

    out_value = codec(json_value)

    assert type(out_value) is type_
    assert out_value == expected


@pytest.mark.parametrize(
    ["type_", "json_list", "expected"],
    [
        (list[int], [123, "123", 123.0], [123, 123, 123]),
        (list[float], [123, "123.1", 123.1], [123.0, 123.1, 123.1]),
        (list[str], [123, "123.1", 123.1], ["123", "123.1", "123.1"]),
        (
            list[datetime],
            [
                1667995689,
                "2022-11-09T12:08:09.123456+01:00",
                1667995689.123456,
            ],
            [
                datetime(2022, 11, 9, 12, 8, 9, 0, timezone.utc),
                datetime(2022, 11, 9, 11, 8, 9, 123456, timezone.utc),
                datetime(2022, 11, 9, 12, 8, 9, 123456, timezone.utc),
            ],
        ),
        (
            list[UUID],
            ["01" * 16, "23" * 16],
            [UUID("01" * 16), UUID("23" * 16)],
        ),
    ],
)
def test_converts_list_of_single_values(
    type_: type[list[Any]],
    json_list: list[Any],
    expected: list[Any],
) -> None:
    codec = make_json_decoder(type_)

    out_value = codec(json_list)

    assert out_value == expected


@pytest.mark.parametrize(
    ["type_", "value", "expected"],
    [
        (set[int], [121, "122", 123.0], set([121, 122, 123])),
        (frozenset[int], [121, "122", 123.0], frozenset([121, 122, 123])),
    ],
)
def test_converts_sets(
    type_: type,
    value: list[Any],
    expected: Any,
) -> None:
    codec: Codec[JsonValue, Any] = make_json_decoder(type_)

    out_value = codec(value)

    assert out_value == expected


def test_list_raises_on_unannotated_list() -> None:
    with pytest.raises(TypeError):
        make_json_decoder(list)  # type: ignore


def test_list_raises_on_list_of_multiple_types() -> None:
    with pytest.raises(TypeError):
        make_json_decoder(list[int, str])  # type: ignore


def test_list_raises_on_not_list() -> None:
    codec = make_json_decoder(list[int])

    with pytest.raises(CodecError):
        codec(123)


@pytest.mark.parametrize(
    ["type_", "json_list", "expected"],
    [
        (tuple[int, ...], [123, "123", 123.0], (123, 123, 123)),
        (tuple[float, ...], [123, "123.1", 123.1], (123.0, 123.1, 123.1)),
        (tuple[str, ...], [123, "123.1", 123.1], ("123", "123.1", "123.1")),
        (
            tuple[datetime, ...],
            [
                1667995689,
                "2022-11-09T12:08:09.123456+01:00",
                1667995689.123456,
            ],
            (
                datetime(2022, 11, 9, 12, 8, 9, 0, timezone.utc),
                datetime(2022, 11, 9, 11, 8, 9, 123456, timezone.utc),
                datetime(2022, 11, 9, 12, 8, 9, 123456, timezone.utc),
            ),
        ),
        (
            tuple[UUID, ...],
            ["01" * 16, "23" * 16],
            (UUID("01" * 16), UUID("23" * 16)),
        ),
    ],
)
def test_converts_tuple_of_single_values(
    type_: type[Any],
    json_list: list[Any],
    expected: list[Any],
) -> None:
    codec = make_json_decoder(type_)

    out_value = codec(json_list)

    assert out_value == expected


def test_tuple_raises_on_not_list() -> None:
    codec = make_json_decoder(tuple[int, ...])

    with pytest.raises(CodecError):
        codec(123)


@dataclass(slots=True, frozen=True)
class TupleData:
    values: tuple[int, str, float, tuple[str, ...]]


def test_tuple_of_multiple_types_raises_on_not_list() -> None:
    codec = make_json_decoder(TupleData)

    with pytest.raises(CodecError):
        codec({"values": 7})


def test_tuple_of_multiple_types_raises_on_unexpected_list_size() -> None:
    codec = make_json_decoder(TupleData)

    with pytest.raises(CodecError):
        codec({"values": [1, 2, 3]})


def test_tuple_raises_on_unannotated_tuple() -> None:
    @dataclass
    class T:
        values: tuple

    with pytest.raises(TypeError):
        make_json_decoder(T)


def test_converts_tuple_of_multiple_types() -> None:
    codec = make_json_decoder(TupleData)

    out_value = codec({"values": (123.0, 123.12, "123.12", (1, "2", 3.0))})

    assert out_value == TupleData(
        values=(123, "123.12", 123.12, ("1", "2", "3.0"))
    )


@dataclass(slots=True, frozen=True)
class Data:
    bvalue: bool
    ivalue: int
    fvalue: float
    svalue: str


def test_parses_json_plain_data() -> None:
    codec = make_json_decoder(Data)

    out_value = codec(
        {
            "bvalue": True,
            "ivalue": 123,
            "fvalue": 123.456,
            "svalue": "string-value",
        }
    )

    assert out_value == Data(
        bvalue=True, ivalue=123, fvalue=123.456, svalue="string-value"
    )


def test_parses_and_converts_json_plain_data() -> None:
    codec = make_json_decoder(Data)

    out_value = codec(
        {
            "bvalue": "true",
            "ivalue": "123",
            "fvalue": "123.456",
            "svalue": 3333,
        }
    )

    assert out_value == Data(
        bvalue=True, ivalue=123, fvalue=123.456, svalue="3333"
    )


@pytest.mark.parametrize("value", ["", "abc", 123, None, [], set()])
def test_raises_on_invalid_value(value: Any) -> None:
    codec = make_json_decoder(Data)

    with pytest.raises(CodecError):
        codec(value)


@dataclass(slots=True, frozen=True)
class OptionalData:
    ivalue: int | None
    fvalue: float | None
    svalue: str | None


def test_parses_json_optional_plain_data() -> None:
    codec = make_json_decoder(OptionalData)

    out_value = codec({"ivalue": None, "fvalue": None, "svalue": None})

    assert out_value == OptionalData(ivalue=None, fvalue=None, svalue=None)


def test_parses_and_converts_json_optional_plain_data() -> None:
    codec = make_json_decoder(OptionalData)

    out_value = codec({"ivalue": "123", "fvalue": "123.456", "svalue": 3333})

    assert out_value == OptionalData(ivalue=123, fvalue=123.456, svalue="3333")


def test_parses_optional_object_as_none() -> None:
    codec: Codec[JsonValue, Data | None] = make_json_decoder(Data | None)

    out_value = codec(None)

    assert out_value is None


def test_parses_optional_object_as_object() -> None:
    codec: Codec[JsonValue, Data | None] = make_json_decoder(Data | None)

    out_value = codec(
        {
            "bvalue": "true",
            "ivalue": "123",
            "fvalue": "123.456",
            "svalue": 3333,
        }
    )

    assert out_value == Data(
        bvalue=True, ivalue=123, fvalue=123.456, svalue="3333"
    )


def test_parses_dict_object() -> None:
    codec = make_json_decoder(dict[int, Data])

    out_value = codec(
        {
            "10": {
                "bvalue": 1,
                "ivalue": "123",
                "fvalue": "123.456",
                "svalue": 3333,
            },
            "20": {
                "bvalue": 0,
                "ivalue": "124",
                "fvalue": "124.456",
                "svalue": 3334,
            },
        }
    )

    assert out_value == {
        10: Data(bvalue=True, ivalue=123, fvalue=123.456, svalue="3333"),
        20: Data(bvalue=False, ivalue=124, fvalue=124.456, svalue="3334"),
    }


def test_dict_raises_on_invalid_value() -> None:
    codec = make_json_decoder(dict[int, str])

    with pytest.raises(CodecError):
        codec("123")


def test_dict_raises_on_unannotated_dict() -> None:
    with pytest.raises(TypeError):
        make_json_decoder(dict)


def test_dict_raises_on_badly_annotated_dict() -> None:
    with pytest.raises(TypeError):
        make_json_decoder(dict[int, str, float])  # type: ignore


@dataclass(slots=True, frozen=True)
class DeprecatedFields:
    a_list: List[int]
    a_tuple: Tuple[int, ...]
    a_dict: Dict[str, int]
    a_union: Union[int, str]
    a_set: Set[int]
    a_frozenset: FrozenSet[int]


def test_supports_deprecated_typing_classes() -> None:
    codec = make_json_decoder(DeprecatedFields)

    out_value = codec(
        {
            "a_list": [1, "2"],
            "a_tuple": [3.0, "4"],
            "a_dict": {"a": "7"},
            "a_union": "123a",
            "a_set": ["1", 2, 3.0],
            "a_frozenset": ["1", 2, 3.0],
        }
    )

    assert out_value == DeprecatedFields(
        a_list=[1, 2],
        a_tuple=(3, 4),
        a_dict={"a": 7},
        a_union="123a",
        a_set={1, 2, 3},
        a_frozenset=frozenset({1, 2, 3}),
    )


class Enumerate(Enum):
    IVAL = 1
    SVAL = "string-value"
    FVAL = 1.2


@pytest.mark.parametrize(
    ["json_value", "expected"],
    [
        ("IVAL", Enumerate.IVAL),
        ("SVAL", Enumerate.SVAL),
        ("FVAL", Enumerate.FVAL),
    ],
)
def test_converts_enum(json_value: str, expected: Enumerate) -> None:
    codec = make_json_decoder(Enumerate)

    out_value = codec(json_value)

    assert out_value is expected


def test_enum_raises_on_unknown_name() -> None:
    codec = make_json_decoder(Enumerate)

    with pytest.raises(CodecError):
        codec("unknown")


def test_enum_raises_on_not_a_string() -> None:
    codec = make_json_decoder(Enumerate)

    with pytest.raises(CodecError):
        codec(1)
