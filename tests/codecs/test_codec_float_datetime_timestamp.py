from datetime import datetime, timedelta, timezone

import pytest

from modern.codecs import CodecError
from modern.codecs.codec_float_datetime_timestamp import (
    DatetimeToFloatTimestampCodec,
    FloatToDatetimeTimestampCodec,
)

utc_plus_2 = timezone(timedelta(hours=2))


def test_float_to_datetime_timestamp() -> None:
    codec = FloatToDatetimeTimestampCodec(default_tz=utc_plus_2)
    value = 7328.2323

    out_value = codec(value)

    assert type(out_value) is datetime
    assert out_value == datetime(
        1970, 1, 1, 2, 2, 8, 232300, tzinfo=timezone.utc
    )


def test_float_to_datetime_timestamp_raises_for_overflowed_timestamp() -> None:
    codec = FloatToDatetimeTimestampCodec(default_tz=utc_plus_2)
    value = 999999999999.99

    with pytest.raises(CodecError):
        codec(value)


def test_datetime_to_float_timestamp() -> None:
    codec = DatetimeToFloatTimestampCodec(default_tz=utc_plus_2)
    value = datetime(1970, 1, 1, 2, 2, 8, 232300, tzinfo=timezone.utc)

    out_value = codec(value)

    assert type(out_value) is float
    assert out_value == 7328.2323


def test_datetime_to_float_timestamp_for_naive_datetime() -> None:
    codec = DatetimeToFloatTimestampCodec(default_tz=utc_plus_2)
    value = datetime(1970, 1, 1, 2, 2, 8, 232300)

    out_value = codec(value)

    assert type(out_value) is float
    assert out_value == 128.2323
