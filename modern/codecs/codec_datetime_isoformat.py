from datetime import datetime, timezone

from .base import Codec, CodecError


class IsoformatCodec(Codec[datetime]):
    name = "isoformat"

    def __init__(self, default_tz: timezone) -> None:
        self._default_tz = default_tz

    def in_(self, data: bytes) -> datetime:
        try:
            dt = datetime.fromisoformat(data.decode())
        except ValueError as e:
            raise CodecError(data) from e
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._default_tz)
        return dt

    def out(self, value: datetime) -> bytes:
        return value.isoformat().encode()
