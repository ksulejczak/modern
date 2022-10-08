from uuid import UUID

from .base import Codec, CodecError


class UuidCodec(Codec[UUID]):
    name = "uuid"

    def in_(self, data: bytes) -> UUID:
        try:
            return UUID(data.decode())
        except ValueError as e:
            raise CodecError(data) from e

    def out(self, value: UUID) -> bytes:
        return value.hex.encode()
