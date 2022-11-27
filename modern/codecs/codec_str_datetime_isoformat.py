from datetime import datetime, timezone

from .base import Codec, CodecError


class StrToDatetimeIsoformatCodec(Codec[str, datetime]):
    def __init__(self, default_tz: timezone) -> None:
        self._default_tz = default_tz

    def __call__(self, data: str) -> datetime:
        try:
            dt = datetime.fromisoformat(data)
        except ValueError as e:
            raise CodecError(data) from e
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._default_tz)
        return dt


class DatetimeToStrIsoformatCodec(Codec[datetime, str]):
    def __init__(self, default_tz: timezone) -> None:
        self._default_tz = default_tz

    def __call__(self, data: datetime) -> str:
        if data.tzinfo is None:
            data = data.replace(tzinfo=self._default_tz)
        return data.isoformat()
