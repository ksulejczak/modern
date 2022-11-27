from datetime import datetime, timedelta, timezone

import pytest

from modern.codecs import CodecError
from modern.codecs.codec_str_datetime_isoformat import (
    DatetimeToStrIsoformatCodec,
    StrToDatetimeIsoformatCodec,
)

utc_plus_2 = timezone(timedelta(hours=2))
utc_plus_3 = timezone(timedelta(hours=3))


@pytest.mark.parametrize(
    ["isoformat", "expected"],
    [
        ("2022-10-04", datetime(2022, 10, 4, 0, 0, 0, tzinfo=utc_plus_2)),
        (
            "2022-10-04T19:53",
            datetime(2022, 10, 4, 19, 53, 0, tzinfo=utc_plus_2),
        ),
        (
            "2022-10-04 19:53",
            datetime(2022, 10, 4, 19, 53, 0, tzinfo=utc_plus_2),
        ),
        (
            "2022-10-04 19:53.123",
            datetime(2022, 10, 4, 19, 53, 0, 123000, tzinfo=utc_plus_2),
        ),
        (
            "2022-10-04 19:53.123+03:00",
            datetime(2022, 10, 4, 18, 53, 0, 123000, tzinfo=utc_plus_2),
        ),
    ],
)
def test_str_to_datetime_isoformat(isoformat: str, expected: datetime) -> None:
    codec = StrToDatetimeIsoformatCodec(default_tz=utc_plus_2)

    out_value = codec(isoformat)

    assert type(out_value) is datetime
    assert out_value == expected


def test_in_raises_not_recognized_timestamp() -> None:
    codec = StrToDatetimeIsoformatCodec(default_tz=utc_plus_2)
    value = "20222-10-20"

    with pytest.raises(CodecError):
        codec(value)


@pytest.mark.parametrize(
    ["dt", "expected"],
    [
        (
            datetime(2022, 10, 4, 0, 0, 0, tzinfo=utc_plus_2),
            "2022-10-04T00:00:00+02:00",
        ),
        (
            datetime(2022, 10, 4, 19, 53, 0),
            "2022-10-04T19:53:00+02:00",
        ),
        (
            datetime(2022, 10, 4, 19, 53, 0, tzinfo=utc_plus_2),
            "2022-10-04T19:53:00+02:00",
        ),
        (
            datetime(2022, 10, 4, 19, 53, 0, 123000, tzinfo=utc_plus_2),
            "2022-10-04T19:53:00.123000+02:00",
        ),
        (
            datetime(2022, 10, 4, 18, 53, 0, 123000, tzinfo=utc_plus_3),
            "2022-10-04T18:53:00.123000+03:00",
        ),
    ],
)
def test_datetime_to_str_isoformat(dt: datetime, expected: str) -> None:
    codec = DatetimeToStrIsoformatCodec(default_tz=utc_plus_2)

    out_value = codec(dt)

    assert type(out_value) is str
    assert out_value == expected
