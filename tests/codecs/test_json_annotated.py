import json
from dataclasses import dataclass
from typing import Annotated, Any

import pytest

from modern.codecs.json import (
    CodecError,
    make_json_deserializer,
    make_json_serializer,
)
from modern.codecs.validators import LengthRange, ValueRange


@dataclass(slots=True, frozen=True)
class Data:
    a_str: Annotated[str, ValueRange(gte="kkk"), LengthRange(4, 5)]
    a_int: Annotated[int, ValueRange(gte=1, lt=10)]
    ignored: Annotated[int, lambda x: x] = 1_000


@pytest.mark.parametrize(
    "value",
    [
        {"a_str": "123456", "a_int": 1},
        {"a_str": "jjj", "a_int": 1},
        {"a_str": "12345", "a_int": 0},
        {"a_str": "12345", "a_int": 10},
    ],
)
def test_raises_on_validation_failure(value: dict[str, Any]) -> None:
    deserializer = make_json_deserializer(Data)

    with pytest.raises(CodecError):
        deserializer(json.dumps(value).encode())


def test_deserializes_annotated_types() -> None:
    serializer = make_json_serializer(Data)
    deserializer = make_json_deserializer(Data)
    data = Data(a_str="kkkk", a_int=2)

    restored = deserializer(serializer(data))

    assert data == restored
