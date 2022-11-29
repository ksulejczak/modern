from collections.abc import Callable
from dataclasses import dataclass

import pytest

from modern.codecs.json import (
    CodecError,
    JsonValue,
    make_json_deserializer,
    make_json_serializer,
)
from modern.codecs.json_helpers import (
    orjson_dump,
    orjson_load,
    simplejson_dump,
    simplejson_load,
    std_load,
    ujson_dump,
    ujson_load,
)


@dataclass(slots=True, frozen=True)
class Data:
    a_float: float
    a_str: str
    a_maybe_int: int | None


def test_serialize_deserialize() -> None:
    data = Data(
        a_float=1.23,
        a_str="frodo-baggins",
        a_maybe_int=None,
    )
    serializer = make_json_serializer(Data)
    deserializer = make_json_deserializer(Data)

    serialized = serializer(data)

    assert type(serialized) is bytes

    restored = deserializer(serialized)

    assert restored == data


@pytest.mark.parametrize(
    "json_dump",
    [orjson_dump, ujson_dump, simplejson_dump],
)
def test_serialize_function(json_dump: Callable[[JsonValue], bytes]) -> None:
    data = Data(
        a_float=1.23,
        a_str="frodo-baggins",
        a_maybe_int=None,
    )
    # use non-standard serializer and standard deserializer
    serializer = make_json_serializer(Data, json_dump=json_dump)
    deserializer = make_json_deserializer(Data)

    serialized = serializer(data)

    assert type(serialized) is bytes

    restored = deserializer(serialized)

    assert restored == data


@pytest.mark.parametrize(
    "json_load",
    [orjson_load, ujson_load, simplejson_load],
)
def test_deserialize_function(json_load: Callable[[bytes], JsonValue]) -> None:
    data = Data(
        a_float=1.23,
        a_str="frodo-baggins",
        a_maybe_int=None,
    )
    # use standard serializer and non-standard deserializer
    serializer = make_json_serializer(Data)
    deserializer = make_json_deserializer(Data, json_load=json_load)

    serialized = serializer(data)

    assert type(serialized) is bytes

    restored = deserializer(serialized)

    assert restored == data


@pytest.mark.parametrize(
    "json_load",
    [std_load, orjson_load, ujson_load, simplejson_load],
)
def test_deserialize_function_raises_on_invalid_value(
    json_load: Callable[[bytes], JsonValue]
) -> None:
    deserializer = make_json_deserializer(Data, json_load=json_load)

    with pytest.raises(CodecError):
        deserializer(int)  # type: ignore[arg-type]
