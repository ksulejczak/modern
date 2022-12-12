from __future__ import annotations

__all__ = [
    "make_json_decoder",
    "make_json_deserializer",
    "make_json_encoder",
    "make_json_serializer",
]

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from inspect import isclass
from types import UnionType
from typing import Any, Generic, TypeVar, get_args, get_origin, overload
from uuid import UUID

from ..compat import AnnotatedType, EnumType, GenericAliases, UnionTypes
from . import instances
from .base import Codec, CodecError, CombinedCodec, NoopCodec
from .json_helpers import std_dump, std_load
from .types import JsonPlainValue, JsonValue
from .validators import Validator

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


def make_json_decoder(dclass: Any) -> Codec[JsonValue, Any]:
    known_codec = _PLAIN_CODEC_MAPPING.get(dclass)
    if known_codec is not None:
        return known_codec

    if isinstance(dclass, GenericAliases):
        origin = get_origin(dclass)
        if origin is list or origin is set or origin is frozenset:
            return _make_sequence_decoder(dclass)
        if origin is tuple:
            return _make_tuple_decoder(dclass)
        if origin is dict:
            return _make_mapping_decoder(dclass)
    if isinstance(dclass, AnnotatedType):
        return _make_annotated_decoder(dclass)
    if isinstance(dclass, UnionTypes):
        return _make_union_decoder(dclass)
    if issubclass(dclass, Enum):
        return _make_enum_decoder(dclass)
    return _make_dataclass_decoder(dclass)


class _BytesToJson(Codec[bytes, JsonValue]):
    def __init__(self, json_load: Callable[[bytes], JsonValue]) -> None:
        self._json_load = json_load

    def __call__(self, data: bytes) -> JsonValue:
        try:
            return self._json_load(data)
        except (ValueError, TypeError) as e:
            raise CodecError(data) from e


def make_json_deserializer(
    dclass: type[JDT],
    json_load: Callable[[bytes], JsonValue] = std_load,
) -> Codec[bytes, JDT]:
    codec = make_json_decoder(dclass)
    bytes_to_json_codec = _BytesToJson(json_load)
    return CombinedCodec(bytes_to_json_codec, codec)


class _NoopCodecWithTypecheck(Codec):
    def __init__(self, type_: type) -> None:
        self._type = type_

    def __call__(self, data: Any) -> Any:
        if not isinstance(data, self._type):
            raise CodecError(data)
        return data


_PLAIN_ENCODER_MAPPING = {
    None.__class__: _NoopCodecWithTypecheck(None.__class__),
    bool: _NoopCodecWithTypecheck(bool),
    int: _NoopCodecWithTypecheck(int),
    float: _NoopCodecWithTypecheck(float),
    str: _NoopCodecWithTypecheck(str),
    datetime: instances.datetime_to_str_isoformat_utc,
    UUID: instances.uuid_to_str,
}

_STR_CODECS: dict[type, Codec] = {
    bool: instances.bool_to_str,
    int: instances.int_to_str,
    float: instances.float_to_str,
    str: NoopCodec(),
    datetime: instances.datetime_to_str_isoformat_utc,
    UUID: instances.uuid_to_str,
}


JET = TypeVar("JET")


def make_json_encoder(dclass: type[JET]) -> Codec[JET, JsonValue]:
    known_codec = _PLAIN_ENCODER_MAPPING.get(dclass)
    if known_codec is not None:
        return known_codec

    if isinstance(dclass, GenericAliases):
        origin = get_origin(dclass)
        if isclass(origin):
            if issubclass(origin, Mapping):
                return _make_mapping_encoder(dclass)
            if issubclass(origin, tuple):
                return _make_tuple_encoder(dclass)
            if issubclass(origin, Iterable):
                return _make_list_encoder(dclass)

    if isinstance(dclass, AnnotatedType):
        return _make_annotated_encoder(dclass)
    if isinstance(dclass, UnionTypes):
        return _make_union_encoder(dclass)
    if issubclass(dclass, Enum):
        return _make_enum_encoder(dclass)
    return _make_dataclass_encoder(dclass)


class _JsonToBytes(Codec[JsonValue, bytes]):
    def __init__(self, json_dump: Callable[[JsonValue], bytes]) -> None:
        self._json_dump = json_dump

    def __call__(self, data: JsonValue) -> bytes:
        return self._json_dump(data)


def make_json_serializer(
    dclass: type[JDT],
    json_dump: Callable[[JsonValue], bytes] = std_dump,
) -> Codec[JDT, bytes]:
    codec = make_json_encoder(dclass)
    json_to_bytes_codec = _JsonToBytes(json_dump)
    return CombinedCodec(codec, json_to_bytes_codec)


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
        if not isinstance(data, Iterable):
            raise CodecError(data)
        return self._container_factory(map(self._plain_codec, data))


def _make_sequence_decoder(dclass: Any) -> Codec[JsonValue, Any]:
    args = get_args(dclass)
    if len(args) != 1:
        raise TypeError("Cannot handle type", dclass)
    item_decoder = make_json_decoder(args[0])
    return _ContainerCodec(
        item_decoder,
        get_origin(dclass),  # type: ignore[arg-type]
    )


TTP = TypeVar("TTP")


class _TupleCodec(Codec[JsonValue, TTP]):
    def __init__(
        self,
        item_codecs: Sequence[Codec[JsonValue, Any]],
    ) -> None:
        self._item_codecs = item_codecs

    def __call__(self, data: JsonValue) -> TTP:
        if not isinstance(data, Sequence):
            raise CodecError(data)
        if len(data) != len(self._item_codecs):
            raise CodecError(data)
        return tuple(  # type: ignore
            c(v) for c, v in zip(self._item_codecs, data)
        )


TDT = TypeVar("TDT")


def _make_tuple_decoder(dclass: Any) -> Codec[JsonValue, TDT]:
    args = get_args(dclass)
    if len(args) == 2 and args[1] is Ellipsis:
        # handle `tuple[type, ...]` - this case is similar to `list[type]`
        item_decoder = make_json_decoder(args[0])
        return _ContainerCodec(
            item_decoder,
            get_origin(dclass),  # type: ignore[arg-type]
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


def _make_mapping_decoder(dclass: Any) -> Codec[JsonValue, MDT]:
    args = dclass.__args__
    if len(args) != 2:
        raise TypeError("Cannot handle type", dclass)
    key_codec: Codec[str, Any] = make_json_decoder(  # type: ignore[assignment]
        args[0]
    )
    value_codec: Codec[JsonValue, Any] = make_json_decoder(args[1])
    return _MappingCodec(key_codec, value_codec)  # type: ignore[return-value]


def _make_union_decoder(dclass: Any) -> Codec:
    args = get_args(dclass)
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


class _CodecWithValidators(Codec):
    def __init__(
        self, codec: Codec, validators: tuple[Validator, ...]
    ) -> None:
        self._codec = codec
        self._validators = validators

    def __call__(self, data: Any) -> Any:
        value = self._codec(data)
        for validator in self._validators:
            if validator(value) is False:
                raise CodecError("Validation failed", value, validator)
        return value


def _make_annotated_decoder(dclass: Any) -> Codec:
    args = get_args(dclass)
    codec = make_json_decoder(args[0])
    validators = tuple(
        validator for validator in args[1:] if isinstance(validator, Validator)
    )
    if not validators:
        return codec
    else:
        return _CodecWithValidators(codec, validators)


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
        try:
            return self._factory(**kw)
        except TypeError as e:
            raise CodecError(data) from e


DCT = TypeVar("DCT")


def _make_dataclass_decoder(dclass: type[DCT]) -> Codec[JsonValue, DCT]:
    codec_by_name = {}
    for field in fields(dclass):
        codec_by_name[field.name] = make_json_decoder(field.type)

    return _ObjectCodec(codec_by_name, dclass)


class _ContainerEncoder(Codec):
    def __init__(self, item_encoder: Codec) -> None:
        self._item_encoder = item_encoder

    def __call__(self, data: Iterable) -> list:
        if not isinstance(data, Iterable):
            raise CodecError(data)
        return list(map(self._item_encoder, data))


class _StructEncoder(Codec):
    def __init__(self, encoders: list[Codec]) -> None:
        self._encoders = encoders

    def __call__(self, data: Sequence) -> list[Any]:
        if not isinstance(data, Sequence):
            raise CodecError(data)
        if len(data) != len(self._encoders):
            raise CodecError(data)
        return [codec(item) for item, codec in zip(data, self._encoders)]


def _make_tuple_encoder(dclass: Any) -> Codec:
    args = get_args(dclass)
    if len(args) == 2 and args[1] is Ellipsis:
        item_encoder = make_json_encoder(args[0])
        return _ContainerEncoder(item_encoder)
    else:
        encoders = list(map(make_json_encoder, args))
        return _StructEncoder(encoders)


def _make_list_encoder(dclass: Any) -> Codec:
    args = get_args(dclass)
    if len(args) != 1:
        raise TypeError("Cannot handle type", dclass)
    item_encoder = make_json_encoder(args[0])
    return _ContainerEncoder(item_encoder)


class _MappingEncoder(Codec):
    def __init__(self, key_codec: Codec, value_codec: Codec) -> None:
        self._key_codec = key_codec
        self._value_codec = value_codec

    def __call__(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, Mapping):
            raise CodecError(data)
        d = {}
        for key, value in data.items():
            encoded_key = self._key_codec(key)
            encoded_value = self._value_codec(value)
            d[encoded_key] = encoded_value
        return d


def _make_mapping_encoder(dclass: Any) -> Codec:
    args = get_args(dclass)
    if len(args) != 2:
        raise TypeError("Cannot handle type", dclass)
    key_codec = _STR_CODECS.get(args[0])
    if key_codec is None:
        raise TypeError("Cannot use type as dictionary key", dclass)
    value_codec: Codec[JsonValue, Any] = make_json_encoder(args[1])
    return _MappingEncoder(key_codec, value_codec)


class _UnionEncoder(Codec):
    def __init__(self, types_encoder: list[Codec[Any, JsonValue]]):
        self._types_encoder = types_encoder

    def __call__(self, data: Any) -> JsonValue:
        for codec in self._types_encoder:
            try:
                return codec(data)
            except CodecError:
                pass
        else:
            raise CodecError(data)


def _make_union_encoder(dclass: Any) -> Codec:
    encoders = list(map(make_json_encoder, get_args(dclass)))
    return _UnionEncoder(encoders)


class _EnumEncoder(Codec):
    def __call__(self, data: Enum) -> str:
        return data.name


_ENUM_ENCODER = _EnumEncoder()


def _make_enum_encoder(dclass: EnumType) -> Codec:
    return _ENUM_ENCODER


class _ObjectEncoder(Codec):
    def __init__(
        self,
        type_: type,
        field_codecs: Mapping[str, Codec],
    ) -> None:
        self._type = type_
        self._field_codecs = field_codecs

    def __call__(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, self._type):
            raise CodecError(data)
        d = {}
        for name, codec in self._field_codecs.items():
            d[name] = codec(getattr(data, name))

        return d


def _make_dataclass_encoder(dclass: Any) -> Codec:
    codec_by_name = {}
    for field in fields(dclass):
        codec_by_name[field.name] = make_json_encoder(field.type)

    return _ObjectEncoder(dclass, codec_by_name)


def _make_annotated_encoder(dclass: Any) -> Codec:
    args = get_args(dclass)
    return make_json_encoder(args[0])
