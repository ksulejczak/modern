from uuid import UUID

from .base import Codec, CodecError


class StrToUuidCodec(Codec[str, UUID]):
    def __call__(self, data: str) -> UUID:
        try:
            return UUID(data)
        except ValueError as e:
            raise CodecError(data) from e


class UuidToStrCodec(Codec[UUID, str]):
    def __call__(self, data: UUID) -> str:
        return data.hex
