from datetime import datetime, timezone

import pytest

from modern.codecs.instances import str_to_datetime_isoformat_timestamp_utc


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        (
            "2022-10-28T01:02:03",
            datetime(2022, 10, 28, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            "7201.12",
            datetime(1970, 1, 1, 2, 0, 1, 120000, tzinfo=timezone.utc),
        ),
    ],
)
def test_str_to_datetime(value: str, expected: datetime) -> None:
    out_value = str_to_datetime_isoformat_timestamp_utc(value)

    assert out_value == expected
