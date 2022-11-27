from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Set, Tuple, Union
from uuid import UUID

import pytest

from modern.codecs import Codec, CodecError
from modern.codecs.json_converter import JsonValue, make_json_encoder


def test_raises_on_unknown_type() -> None:
    class _T:
        pass

    with pytest.raises(TypeError):
        make_json_encoder(_T)


def test_raises_on_invalid_json_value() -> None:
    codec = make_json_encoder(int)

    with pytest.raises(CodecError):
        codec(set())  # type: ignore


def test_raises_on_none_for_not_optional_field() -> None:
    codec = make_json_encoder(int)

    with pytest.raises(CodecError):
        codec(None)  # type: ignore[arg-type]


@pytest.mark.parametrize("type_", [list, tuple])
def test_raises_if_container_type_not_annotated(
    type_: type[list] | type[tuple],
) -> None:
    with pytest.raises(TypeError):
        make_json_encoder(type_)


@pytest.mark.parametrize(
    ["type_", "value", "expected"],
    [
        (bool, True, True),
        (bool, False, False),
        (int, 123, 123),
        (float, 123.1, 123.1),
        (str, "123", "123"),
        (
            datetime,
            datetime(2022, 11, 9, 12, 8, 9, 0, timezone.utc),
            "2022-11-09T12:08:09+00:00",
        ),
        (
            datetime,
            datetime(2022, 11, 9, 11, 8, 9, 123456, timezone.utc),
            "2022-11-09T11:08:09.123456+00:00",
        ),
        (
            datetime,
            datetime(2022, 11, 9, 12, 8, 9, 123456, timezone.utc),
            "2022-11-09T12:08:09.123456+00:00",
        ),
        (UUID, UUID("01" * 16), "01" * 16),
    ],
)
def test_converts_single_value(
    type_: type[Any],
    value: Any,
    expected: JsonValue,
) -> None:
    codec = make_json_encoder(type_)

    out_value = codec(value)

    assert out_value == expected


@pytest.mark.parametrize(
    ["type_", "input_data", "expected"],
    [
        (list[int], (123, 123, 123), [123, 123, 123]),
        (list[float], (123.0, 123.1, 123.1), [123.0, 123.1, 123.1]),
        (list[str], ("123", "123.1", "123.1"), ["123", "123.1", "123.1"]),
        (
            list[datetime],
            (
                datetime(2022, 11, 9, 12, 8, 9, 0, timezone.utc),
                datetime(2022, 11, 9, 11, 8, 9, 123456, timezone.utc),
                datetime(2022, 11, 9, 12, 8, 9, 123456, timezone.utc),
            ),
            [
                "2022-11-09T12:08:09+00:00",
                "2022-11-09T11:08:09.123456+00:00",
                "2022-11-09T12:08:09.123456+00:00",
            ],
        ),
        (
            list[UUID],
            (UUID("01" * 16), UUID("23" * 16)),
            ["01" * 16, "23" * 16],
        ),
    ],
)
def test_converts_list_of_single_values(
    type_: type[list[Any]],
    input_data: list[Any],
    expected: list[Any],
) -> None:
    codec = make_json_encoder(type_)

    out_value = codec(input_data)

    assert out_value == expected


def test_list_raises_on_unannotated_list() -> None:
    with pytest.raises(TypeError):
        make_json_encoder(list)  # type: ignore


def test_list_raises_on_list_of_multiple_types() -> None:
    with pytest.raises(TypeError):
        make_json_encoder(list[int, str])  # type: ignore


def test_list_raises_on_not_list() -> None:
    codec = make_json_encoder(list[int])

    with pytest.raises(CodecError):
        codec(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ["type_", "input_data", "expected"],
    [
        (tuple[int, ...], (123, 123, 123), [123, 123, 123]),
        (tuple[float, ...], (123.0, 123.1, 123.1), [123.0, 123.1, 123.1]),
        (
            tuple[str, ...],
            ("123", "123.1", "123.1"),
            ["123", "123.1", "123.1"],
        ),
        (
            tuple[datetime, ...],
            (
                datetime(2022, 11, 9, 12, 8, 9, 0, timezone.utc),
                datetime(2022, 11, 9, 11, 8, 9, 123456, timezone.utc),
                datetime(2022, 11, 9, 12, 8, 9, 123456, timezone.utc),
            ),
            [
                "2022-11-09T12:08:09+00:00",
                "2022-11-09T11:08:09.123456+00:00",
                "2022-11-09T12:08:09.123456+00:00",
            ],
        ),
        (
            tuple[UUID, ...],
            (UUID("01" * 16), UUID("23" * 16)),
            ["01" * 16, "23" * 16],
        ),
    ],
)
def test_converts_tuple_of_single_values(
    type_: type[Any],
    input_data: list[Any],
    expected: list[Any],
) -> None:
    codec = make_json_encoder(type_)

    out_value = codec(input_data)

    assert out_value == expected


def test_tuple_raises_on_not_list() -> None:
    codec = make_json_encoder(tuple[int, ...])

    with pytest.raises(CodecError):
        codec(123)  # type: ignore[arg-type]


@dataclass(slots=True, frozen=True)
class TupleData:
    values: tuple[int, str, float, tuple[str, ...]]


def test_tuple_of_multiple_types_raises_on_not_list() -> None:
    codec = make_json_encoder(TupleData)

    with pytest.raises(CodecError):
        codec({"values": 7})  # type: ignore[arg-type]


def test_tuple_of_multiple_types_raises_on_unexpected_list_size() -> None:
    codec = make_json_encoder(TupleData)

    with pytest.raises(CodecError):
        codec({"values": [1, 2, 3]})  # type: ignore[arg-type]


def test_tuple_raises_on_unannotated_tuple() -> None:
    @dataclass
    class T:
        values: tuple

    with pytest.raises(TypeError):
        make_json_encoder(T)


def test_converts_tuple_of_multiple_types() -> None:
    codec = make_json_encoder(TupleData)

    out_value = codec(
        TupleData(values=(123, "123.12", 123.12, ("1", "2", "3.0")))
    )

    assert out_value == (
        {"values": [123, "123.12", 123.12, ["1", "2", "3.0"]]}
    )


def test_raises_on_no_sequence() -> None:
    codec = make_json_encoder(TupleData)

    with pytest.raises(CodecError):
        codec(
            TupleData(
                values=7,  # type: ignore[arg-type]
            )
        )


def test_raises_on_unexpected_sequence_length() -> None:
    codec = make_json_encoder(TupleData)

    with pytest.raises(CodecError):
        codec(
            TupleData(
                values=[1],  # type: ignore[arg-type]
            )
        )


@dataclass(slots=True, frozen=True)
class SetData:
    ints: set[int]
    strs: frozenset[str]


def test_coverts_to_sets() -> None:
    codec = make_json_encoder(SetData)

    out_value = codec(
        SetData(
            ints={1, 5, 10},
            strs=frozenset({"a-value", "b-value"}),
        )
    )

    assert isinstance(out_value, Mapping)
    assert isinstance(out_value["ints"], list)
    assert set(out_value["ints"]) == {1, 5, 10}
    assert isinstance(out_value["strs"], list)
    assert set(out_value["strs"]) == {"a-value", "b-value"}


@dataclass(slots=True, frozen=True)
class Data:
    bvalue: bool
    ivalue: int
    fvalue: float
    svalue: str


def test_encodes_json_plain_data() -> None:
    codec = make_json_encoder(Data)

    out_value = codec(
        Data(bvalue=True, ivalue=123, fvalue=123.456, svalue="3333")
    )

    assert out_value == (
        {
            "bvalue": True,
            "ivalue": 123,
            "fvalue": 123.456,
            "svalue": "3333",
        }
    )


@pytest.mark.parametrize("value", ["", "abc", 123, None, [], set()])
def test_raises_on_invalid_value(value: Any) -> None:
    codec = make_json_encoder(Data)

    with pytest.raises(CodecError):
        codec(value)


@dataclass(slots=True, frozen=True)
class OptionalData:
    ivalue: int | None
    fvalue: float | None
    svalue: str | None


def test_encodes_optional_null_data() -> None:
    codec = make_json_encoder(OptionalData)

    out_value = codec(OptionalData(ivalue=None, fvalue=None, svalue=None))

    assert out_value == {"ivalue": None, "fvalue": None, "svalue": None}


def test_encodes_not_null_optional_plain_data() -> None:
    codec = make_json_encoder(OptionalData)

    out_value = codec(OptionalData(ivalue=123, fvalue=123.456, svalue="3333"))

    assert out_value == {"ivalue": 123, "fvalue": 123.456, "svalue": "3333"}


def test_encodes_optional_object_as_none() -> None:
    codec: Codec[Data | None, JsonValue] = make_json_encoder(
        Data | None,  # type: ignore[arg-type]
    )

    out_value = codec(None)

    assert out_value is None


def test_encodes_optional_object_as_object() -> None:
    codec: Codec[Data | None, JsonValue] = make_json_encoder(
        Data | None,  # type: ignore[arg-type]
    )

    out_value = codec(
        Data(bvalue=True, ivalue=123, fvalue=123.456, svalue="3333")
    )

    assert out_value == {
        "bvalue": True,
        "ivalue": 123,
        "fvalue": 123.456,
        "svalue": "3333",
    }


def test_raises_if_no_union_type_matched() -> None:
    codec = make_json_encoder(OptionalData)

    with pytest.raises(CodecError):
        codec(
            OptionalData(
                ivalue=set(),  # type: ignore[arg-type]
                fvalue=123.456,
                svalue="3333",
            )
        )


def test_parses_dict_object() -> None:
    codec = make_json_encoder(dict[int, Data])

    out_value = codec(
        {
            10: Data(bvalue=True, ivalue=123, fvalue=123.456, svalue="3333"),
            20: Data(bvalue=False, ivalue=124, fvalue=124.456, svalue="3334"),
        }
    )

    assert out_value == {
        "10": {
            "bvalue": True,
            "ivalue": 123,
            "fvalue": 123.456,
            "svalue": "3333",
        },
        "20": {
            "bvalue": False,
            "ivalue": 124,
            "fvalue": 124.456,
            "svalue": "3334",
        },
    }


def test_dict_raises_on_invalid_value() -> None:
    codec = make_json_encoder(dict[int, str])

    with pytest.raises(CodecError):
        codec("123")  # type: ignore[arg-type]


def test_dict_raises_on_unannotated_dict() -> None:
    with pytest.raises(TypeError):
        make_json_encoder(dict)


def test_dict_raises_on_badly_annotated_dict() -> None:
    with pytest.raises(TypeError):
        make_json_encoder(dict[int, str, float])  # type: ignore


@dataclass(slots=True, frozen=True)
class DeprecatedFields:
    a_list: List[int]
    a_tuple: Tuple[int, ...]
    a_dict: Dict[str, int]
    a_union: Union[int, str]
    a_set: Set[int]
    a_frozenset: FrozenSet[int]


def test_supports_deprecated_typing_classes() -> None:
    codec = make_json_encoder(DeprecatedFields)

    out_value = codec(
        DeprecatedFields(
            a_list=[1, 2],
            a_tuple=(3, 4),
            a_dict={"a": 7},
            a_union="123a",
            a_set={1, 2, 3},
            a_frozenset=frozenset({1, 2, 3}),
        )
    )

    assert isinstance(out_value, Mapping)
    assert out_value["a_list"] == [1, 2]
    assert out_value["a_tuple"] == [3, 4]
    assert out_value["a_dict"] == {"a": 7}
    assert out_value["a_union"] == "123a"
    assert isinstance(out_value["a_set"], list)
    assert set(out_value["a_set"]) == {1, 2, 3}
    assert isinstance(out_value["a_frozenset"], list)
    assert set(out_value["a_frozenset"]) == {1, 2, 3}


def test_raises_on_invalid_key_type() -> None:
    with pytest.raises(TypeError):
        make_json_encoder(dict[frozenset[str], str])


class EnumData(Enum):
    IVAL = 1
    SVAL = "string-value"
    FVAL = 1.2


@pytest.mark.parametrize(
    ["enum_data", "expected"],
    [
        (EnumData.IVAL, "IVAL"),
        (EnumData.SVAL, "SVAL"),
        (EnumData.FVAL, "FVAL"),
    ],
)
def test_converts_enum(enum_data: EnumData, expected: str) -> None:
    codec = make_json_encoder(EnumData)

    out_value = codec(enum_data)

    assert out_value == expected
