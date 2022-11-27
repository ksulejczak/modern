from dataclasses import dataclass

from modern.codecs.json import make_json_deserializer, make_json_serializer


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
