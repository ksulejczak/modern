from datetime import datetime, timedelta, timezone

import pytest

from modern.codecs import Codec, CodecError
from modern.codecs.codec_datetime_isoformat import IsoformatCodec

utc_plus_2 = timezone(timedelta(hours=2))


@pytest.mark.parametrize(
    ["isoformat", "expected"],
    [
        (b"2022-10-04", datetime(2022, 10, 4, 0, 0, 0, tzinfo=utc_plus_2)),
        (
            b"2022-10-04T19:53",
            datetime(2022, 10, 4, 19, 53, 0, tzinfo=utc_plus_2),
        ),
        (
            b"2022-10-04 19:53",
            datetime(2022, 10, 4, 19, 53, 0, tzinfo=utc_plus_2),
        ),
        (
            b"2022-10-04 19:53.123",
            datetime(2022, 10, 4, 19, 53, 0, 123000, tzinfo=utc_plus_2),
        ),
        (
            b"2022-10-04 19:53.123+03:00",
            datetime(2022, 10, 4, 18, 53, 0, 123000, tzinfo=utc_plus_2),
        ),
    ],
)
def test_in(isoformat: bytes, expected: datetime) -> None:
    codec: Codec[datetime] = IsoformatCodec(default_tz=utc_plus_2)

    in_value = codec.in_(isoformat)

    assert type(in_value) is datetime
    assert in_value == expected


def test_in_raises_not_recognized_timestamp() -> None:
    codec: Codec[datetime] = IsoformatCodec(default_tz=utc_plus_2)
    value = b"20222-10-20"

    with pytest.raises(CodecError):
        codec.in_(value)


def test_out() -> None:
    codec: Codec[datetime] = IsoformatCodec(default_tz=utc_plus_2)
    value = datetime(2022, 10, 4, 19, 53, 12, 874643, tzinfo=utc_plus_2)

    out_value = codec.out(value)

    assert type(out_value) is bytes
    assert out_value == b"2022-10-04T19:53:12.874643+02:00"
