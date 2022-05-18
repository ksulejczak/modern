import pytest

from modern.codecs.base import Codec


def test_in_raises() -> None:
    codec: Codec[int] = Codec()

    with pytest.raises(NotImplementedError):
        codec.in_(b"")


def test_out_raises() -> None:
    codec: Codec[int] = Codec()

    with pytest.raises(NotImplementedError):
        codec.out(1)
