from datetime import timezone

from .base import CombinedCodec
from .codec_bool_int import BoolToIntCodec
from .codec_bool_str import BoolToStrCodec
from .codec_bytes_str import BytesToStrCodec, StrToBytesCodec
from .codec_float_datetime_timestamp import (
    DatetimeToFloatTimestampCodec,
    FloatToDatetimeTimestampCodec,
)
from .codec_float_int import (
    FloatToIntCodec,
    FloatToIntRoundCodec,
    IntToFloatCodec,
)
from .codec_int_bool import IntToBoolCodec
from .codec_str_bool import StrToBoolCodec
from .codec_str_datetime_isoformat import (
    DatetimeToStrIsoformatCodec,
    StrToDatetimeIsoformatCodec,
)
from .codec_str_float import FloatToStrCodec, StrToFloatCodec
from .codec_str_int import IntToStrCodec, StrToIntCodec
from .codec_str_uuid import StrToUuidCodec, UuidToStrCodec

bool_to_int = BoolToIntCodec()
bool_to_str = BoolToStrCodec(true_value="true", false_value="false")
bytes_to_str_utf8 = BytesToStrCodec("utf8")
datetime_to_float_timestamp_utc = DatetimeToFloatTimestampCodec(timezone.utc)
datetime_to_str_isoformat_utc = DatetimeToStrIsoformatCodec(timezone.utc)
float_to_datetime_timestamp_utc = FloatToDatetimeTimestampCodec(timezone.utc)
float_to_int = FloatToIntCodec()
float_to_int_rounded = FloatToIntRoundCodec()
float_to_str = FloatToStrCodec()
int_to_bool = IntToBoolCodec()
int_to_float = IntToFloatCodec()
int_to_str = IntToStrCodec()
str_to_bool = StrToBoolCodec(
    true_values=["true", "yes", "on", "1"],
    false_values=["false", "no", "off", "0"],
)
str_to_bytes_utf8 = StrToBytesCodec("utf8")
str_to_datetime_isoformat_utc = StrToDatetimeIsoformatCodec(timezone.utc)
str_to_float = StrToFloatCodec()
str_to_int = StrToIntCodec()
str_to_uuid = StrToUuidCodec()
uuid_to_str = UuidToStrCodec()

str_to_datetime_timestamp_utc = CombinedCodec(
    str_to_float,
    float_to_datetime_timestamp_utc,
)

str_to_datetime_isoformat_timestamp_utc = (
    str_to_datetime_isoformat_utc | str_to_datetime_timestamp_utc
)
