import abc


class DiagT(abc.ABC):
    @abc.abstractmethod
    def set_flag(self, flag: str) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    def unset_flag(self, flag: str) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    def has_flag(self, flag: str) -> bool:
        ...  # pragma: no cover

    @abc.abstractmethod
    def get_flags(self) -> set[str]:
        ...  # pragma: no cover
