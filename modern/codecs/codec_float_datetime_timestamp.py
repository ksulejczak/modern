from datetime import datetime, tzinfo

from .base import Codec, CodecError


class FloatToDatetimeTimestampCodec(Codec[float, datetime]):
    def __init__(self, default_tz: tzinfo) -> None:
        self._default_tz = default_tz

    def __call__(self, data: float) -> datetime:
        try:
            return datetime.fromtimestamp(data, self._default_tz)
        except (OSError, OverflowError, ValueError) as e:
            raise CodecError(data) from e


class DatetimeToFloatTimestampCodec(Codec[datetime, float]):
    def __init__(self, default_tz: tzinfo) -> None:
        self._default_tz = default_tz

    def __call__(self, data: datetime) -> float:
        if data.tzinfo is None:
            data = data.replace(tzinfo=self._default_tz)
        return data.timestamp()
