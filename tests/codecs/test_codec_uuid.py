from uuid import UUID

import pytest

from modern.codecs import CodecError
from modern.codecs.codec_uuid import UuidCodec


@pytest.mark.parametrize(
    ["input_uuid", "expected"],
    [
        (b"0" * 32, UUID("0" * 32)),
        (
            b"01234567-0123-0123-0123-0123456789ab",
            UUID("012345670123012301230123456789ab"),
        ),
    ],
)
def test_in(input_uuid: bytes, expected: UUID) -> None:
    codec = UuidCodec()

    in_value = codec.in_(input_uuid)

    assert type(in_value) is UUID
    assert in_value == expected


@pytest.mark.parametrize(
    "input_uuid",
    [
        b"",
        b"1",
        b"0az",
        b"{}",
        b"1" * 31,
    ],
)
def test_in_raises_on_not_recognized_input(input_uuid: bytes) -> None:
    codec = UuidCodec()

    with pytest.raises(CodecError):
        codec.in_(input_uuid)


def test_out() -> None:
    codec = UuidCodec()
    value = UUID("0123" * 8)

    out_value = codec.out(value)

    assert type(out_value) is bytes
    assert out_value == b"0123" * 8
