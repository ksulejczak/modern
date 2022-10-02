from datetime import datetime, tzinfo

from .base import Codec, CodecError


class TimestampCodec(Codec[datetime]):
    name = "timestamp"

    def __init__(self, float_codec: Codec[float], default_tz: tzinfo) -> None:
        self._float_codec = float_codec
        self._default_tz = default_tz

    def in_(self, data: bytes) -> datetime:
        try:
            return datetime.fromtimestamp(
                self._float_codec.in_(data), self._default_tz
            )
        except (OSError, OverflowError, ValueError) as e:
            raise CodecError(data) from e

    def out(self, value: datetime) -> bytes:
        return self._float_codec.out(value.timestamp())
