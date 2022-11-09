from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from types import GenericAlias, UnionType
from typing import Any, Generic, TypeVar, overload
from uuid import UUID

from ..compat import EnumType, GenericAliases, UnionTypes
from . import instances
from .base import Codec, CodecError, CombinedCodec, NoopCodec

JsonPlainValue = int | float | str | None
JsonValue = int | float | str | bool | None | list | dict[str, Any]
T = TypeVar("T")
CT = TypeVar("CT")


@dataclass(slots=True, frozen=True)
class PlainCodecs(Generic[T]):
    from_int: Codec[int, T] | None
    from_float: Codec[float, T] | None
    from_str: Codec[str, T] | None
    from_bool: Codec[bool, T] | None
    from_none: Codec[None, T] | None

    def convert(self, value: JsonPlainValue) -> T:
        if isinstance(value, bool):
            # bool must be checked before int as bool is subclass of int
            if self.from_bool is not None:
                return self.from_bool(value)
        elif isinstance(value, int):
            if self.from_int is not None:
                return self.from_int(value)
        elif isinstance(value, float):
            if self.from_float is not None:
                return self.from_float(value)
        elif isinstance(value, str):
            if self.from_str is not None:
                return self.from_str(value)
        elif value is None:
            if self.from_none is not None:
                return self.from_none(value)
        raise CodecError(value)


TCT = TypeVar("TCT")


class _TypeCodec(Codec[JsonPlainValue, TCT]):
    def __init__(self, plain_codecs: PlainCodecs[TCT]) -> None:
        self._plain_codecs = plain_codecs

    def __call__(self, data: JsonPlainValue) -> TCT:
        return self._plain_codecs.convert(data)


PLAIN_NONE_JSON_CODECS: PlainCodecs[None] = PlainCodecs(
    from_int=None,
    from_float=None,
    from_str=None,
    from_bool=None,
    from_none=NoopCodec(),
)
PLAIN_NONE_CODEC: Codec[JsonPlainValue, None] = _TypeCodec(
    PLAIN_NONE_JSON_CODECS
)

PLAIN_BOOL_JSON_CODECS: PlainCodecs[bool] = PlainCodecs(
    from_int=instances.int_to_bool,
    from_float=CombinedCodec(
        instances.float_to_int,
        instances.int_to_bool,
    ),
    from_str=instances.str_to_bool,
    from_bool=NoopCodec(),
    from_none=None,
)
PLAIN_BOOL_CODEC: Codec[JsonPlainValue, bool] = _TypeCodec(
    PLAIN_BOOL_JSON_CODECS
)

PLAIN_INT_JSON_CODECS: PlainCodecs[int] = PlainCodecs(
    from_int=NoopCodec(),
    from_float=instances.float_to_int,
    from_str=instances.str_to_int,
    from_bool=instances.bool_to_int,
    from_none=None,
)
PLAIN_INT_CODEC: Codec[JsonPlainValue, int] = _TypeCodec(PLAIN_INT_JSON_CODECS)

PLAIN_FLOAT_JSON_CODECS: PlainCodecs[float] = PlainCodecs(
    from_int=instances.int_to_float,
    from_float=NoopCodec(),
    from_str=instances.str_to_float,
    from_bool=None,
    from_none=None,
)
PLAIN_FLOAT_CODEC: Codec[JsonPlainValue, float] = _TypeCodec(
    PLAIN_FLOAT_JSON_CODECS
)

PLAIN_STR_JSON_CODECS: PlainCodecs[str] = PlainCodecs(
    from_int=instances.int_to_str,
    from_float=instances.float_to_str,
    from_str=NoopCodec(),
    from_bool=instances.bool_to_str,
    from_none=None,
)
PLAIN_STR_CODEC: Codec[JsonPlainValue, str] = _TypeCodec(PLAIN_STR_JSON_CODECS)

PLAIN_DATETIME_JSON_CODECS: PlainCodecs[datetime] = PlainCodecs(
    from_int=CombinedCodec(
        instances.int_to_float,
        instances.float_to_datetime_timestamp_utc,
    ),
    from_float=instances.float_to_datetime_timestamp_utc,
    from_str=instances.str_to_datetime_isoformat_timestamp_utc,
    from_bool=None,
    from_none=None,
)
PLAIN_DATETIME_CODEC: Codec[JsonPlainValue, datetime] = _TypeCodec(
    PLAIN_DATETIME_JSON_CODECS
)

PLAIN_UUID_JSON_CODECS: PlainCodecs[UUID] = PlainCodecs(
    from_int=None,
    from_float=None,
    from_str=instances.str_to_uuid,
    from_bool=None,
    from_none=None,
)
PLAIN_UUID_CODEC = _TypeCodec(PLAIN_UUID_JSON_CODECS)


_PLAIN_CODEC_MAPPING: Mapping[Any, Codec] = {
    None.__class__: PLAIN_NONE_CODEC,
    bool: PLAIN_BOOL_CODEC,
    int: PLAIN_INT_CODEC,
    float: PLAIN_FLOAT_CODEC,
    str: PLAIN_STR_CODEC,
    datetime: PLAIN_DATETIME_CODEC,
    UUID: PLAIN_UUID_CODEC,
}


JDT = TypeVar("JDT")


@overload
def make_json_decoder(dclass: type[JDT]) -> Codec[JsonValue, JDT]:
    ...  # pragma: no cover


@overload
def make_json_decoder(dclass: UnionType) -> Codec[JsonValue, JDT]:
    ...  # pragma: no cover


def make_json_decoder(dclass):
    known_codec = _PLAIN_CODEC_MAPPING.get(dclass)
    if known_codec is not None:
        return known_codec

    if isinstance(dclass, GenericAliases):
        origin = dclass.__origin__
        if origin is list:
            return _make_list_decoder(dclass)
        if origin is tuple:
            return _make_tuple_decoder(dclass)
        if origin is dict:
            return _make_mapping_decoder(dclass)
    if isinstance(dclass, UnionTypes):
        return _make_union_decoder(dclass)
    if issubclass(dclass, Enum):
        return _make_enum_decoder(dclass)
    return _make_dataclass_decoder(dclass)


CCT = TypeVar("CCT")


class _ContainerCodec(Codec[JsonValue, CCT]):
    def __init__(
        self,
        plain_codec: Codec[JsonValue, Any],
        container_factory: Callable[[Iterable[Any]], CCT],
    ) -> None:
        self._plain_codec = plain_codec
        self._container_factory = container_factory

    def __call__(self, data: JsonValue) -> CCT:
        if type(data) is not list:
            raise CodecError(data)
        return self._container_factory(map(self._plain_codec, data))


def _make_list_decoder(dclass: GenericAlias) -> Codec[JsonValue, Any]:
    args = dclass.__args__
    if len(args) != 1:
        raise TypeError("Cannot handle type", dclass)
    item_decoder = make_json_decoder(args[0])
    return _ContainerCodec(item_decoder, dclass.__origin__)


TTP = TypeVar("TTP")


class _TupleCodec(Codec[JsonValue, TTP]):
    def __init__(
        self,
        item_codecs: Sequence[Codec[JsonValue, Any]],
    ) -> None:
        self._item_codecs = item_codecs

    def __call__(self, data: JsonValue) -> TTP:
        if not isinstance(data, list):
            raise CodecError(data)
        if len(data) != len(self._item_codecs):
            raise CodecError(data)
        return tuple(  # type: ignore
            c(v) for c, v in zip(self._item_codecs, data)
        )


TDT = TypeVar("TDT")


def _make_tuple_decoder(dclass: GenericAlias) -> Codec[JsonValue, TDT]:
    args = dclass.__args__
    if len(args) == 2 and args[1] is Ellipsis:
        # handle `tuple[type, ...]` - this case is similar to `list[type]`
        item_decoder = make_json_decoder(args[0])
        return _ContainerCodec(
            item_decoder,
            dclass.__origin__,
        )
    else:
        codecs = tuple(map(make_json_decoder, args))
        return _TupleCodec(codecs)


MCK = TypeVar("MCK")
MCV = TypeVar("MCV")


class _MappingCodec(Codec[JsonValue, dict[MCK, MCV]]):
    def __init__(
        self,
        key_codec: Codec[str, MCK],
        value_codec: Codec[JsonValue, MCV],
    ) -> None:
        self._key_codec = key_codec
        self._value_codec = value_codec

    def __call__(self, data: JsonValue) -> dict[MCK, MCV]:
        if not isinstance(data, dict):
            raise CodecError(data)
        kw: dict[MCK, MCV] = {}
        for k, v in data.items():
            key = self._key_codec(k)
            value = self._value_codec(v)
            kw[key] = value
        return kw


MDT = TypeVar("MDT")


def _make_mapping_decoder(dclass: GenericAlias) -> Codec[JsonValue, MDT]:
    args = dclass.__args__
    if len(args) != 2:
        raise TypeError("Cannot handle type", dclass)
    key_codec: Codec[str, Any] = make_json_decoder(  # type: ignore[assignment]
        args[0]
    )
    value_codec: Codec[JsonValue, Any] = make_json_decoder(args[1])
    return _MappingCodec(key_codec, value_codec)  # type: ignore[return-value]


def _make_union_decoder(dclass: UnionType) -> Codec:
    args = dclass.__args__
    codec = make_json_decoder(args[0])
    for tp in args[1:]:
        codec = codec | make_json_decoder(tp)
    return codec


class _EnumCodec(Codec):
    def __init__(self, dclass: EnumType) -> None:
        self._dclass = dclass

    def __call__(self, data: JsonValue) -> Enum:
        if isinstance(data, str):
            try:
                return self._dclass[data]
            except KeyError as e:
                raise CodecError(data) from e
        raise CodecError(data)


def _make_enum_decoder(dclass: EnumType) -> Codec:
    return _EnumCodec(dclass)


OT = TypeVar("OT")


class _ObjectCodec(Codec[JsonValue, OT]):
    def __init__(
        self,
        field_mapping: Mapping[str, Codec],
        factory: Callable[..., OT],
    ) -> None:
        self._field_mapping = field_mapping
        self._factory = factory

    def __call__(self, data: JsonValue) -> OT:
        if not isinstance(data, dict):
            raise CodecError(data)
        kw = {}
        for k, v in data.items():
            plain_codec = self._field_mapping.get(k)
            if plain_codec is not None:
                kw[k] = plain_codec(v)
        return self._factory(**kw)


DCT = TypeVar("DCT")


def _make_dataclass_decoder(dclass: type[DCT]) -> Codec[JsonValue, DCT]:
    codec_by_name = {}
    for field in fields(dclass):
        codec_by_name[field.name] = make_json_decoder(field.type)

    return _ObjectCodec(codec_by_name, dclass)
