from datetime import datetime, timedelta, timezone

import pytest

from modern.codecs import Codec, CodecError, FloatCodec
from modern.codecs.codec_timestamp import TimestampCodec

utc_plus_2 = timezone(timedelta(hours=2))


def test_in() -> None:
    codec: Codec[datetime] = TimestampCodec(
        float_codec=FloatCodec(), default_tz=utc_plus_2
    )
    value = b"7328.2323"

    in_value = codec.in_(value)

    assert type(in_value) is datetime
    assert in_value == datetime(
        1970, 1, 1, 2, 2, 8, 232300, tzinfo=timezone.utc
    )


def test_in_raises_not_recognized_timestamp() -> None:
    codec: Codec[datetime] = TimestampCodec(
        float_codec=FloatCodec(), default_tz=utc_plus_2
    )
    value = b"123.5.7"

    with pytest.raises(CodecError):
        codec.in_(value)


def test_in_raises_for_overflowed_timestamp() -> None:
    codec: Codec[datetime] = TimestampCodec(
        float_codec=FloatCodec(), default_tz=utc_plus_2
    )
    value = b"999999999999.99"

    with pytest.raises(CodecError):
        codec.in_(value)


def test_out() -> None:
    codec: Codec[datetime] = TimestampCodec(
        float_codec=FloatCodec(), default_tz=utc_plus_2
    )
    value = datetime(1970, 1, 1, 2, 2, 8, 232300, tzinfo=timezone.utc)

    out_value = codec.out(value)

    assert type(out_value) is bytes
    assert out_value == b"7328.2323"
