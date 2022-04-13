from time import monotonic

from .types import DiagT


class Diag(DiagT):
    def __init__(self) -> None:
        self._flags: set[str] = set()
        self._last_set: dict[str, float] = {}

    def set_flag(self, flag: str) -> None:
        self._flags.add(flag)
        self._last_set[flag] = monotonic()

    def unset_flag(self, flag: str) -> None:
        self._flags.discard(flag)

    def has_flag(self, flag: str) -> bool:
        return flag in self._flags

    def get_flags(self) -> set[str]:
        return set(self._flags)
