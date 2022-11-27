from uuid import UUID

import pytest

from modern.codecs import CodecError
from modern.codecs.codec_str_uuid import StrToUuidCodec, UuidToStrCodec


@pytest.mark.parametrize(
    ["input_uuid", "expected"],
    [
        ("0" * 32, UUID("0" * 32)),
        (
            "01234567-0123-0123-0123-0123456789ab",
            UUID("012345670123012301230123456789ab"),
        ),
    ],
)
def test_in(input_uuid: str, expected: UUID) -> None:
    codec = StrToUuidCodec()

    out_value = codec(input_uuid)

    assert type(out_value) is UUID
    assert out_value == expected


@pytest.mark.parametrize(
    "input_uuid",
    [
        "",
        "1",
        "0az",
        "{}",
        "1" * 31,
    ],
)
def test_in_raises_on_not_recognized_input(input_uuid: str) -> None:
    codec = StrToUuidCodec()

    with pytest.raises(CodecError):
        codec(input_uuid)


def test_out() -> None:
    codec = UuidToStrCodec()
    value = UUID("0123" * 8)

    out_value = codec(value)

    assert type(out_value) is str
    assert out_value == "0123" * 8
