from __future__ import annotations

import abc
from contextlib import AbstractAsyncContextManager, AbstractContextManager


class ServiceT(abc.ABC):
    @abc.abstractmethod
    def add_dependency(self, service: ServiceT) -> ServiceT:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def add_runtime_dependency(self, service: ServiceT) -> ServiceT:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def remove_dependency(self, service: ServiceT) -> ServiceT:
        ...  # pragma: no cover

    @abc.abstractmethod
    def add_context(self, context: AbstractContextManager) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def add_async_context(
        self,
        context: AbstractAsyncContextManager,
    ) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def start(self) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def maybe_start(self) -> bool:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def crash(self, reason: BaseException) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def stop(self) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    def service_reset(self) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def restart(self) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def wait_until_stopped(self) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    def set_shutdown(self) -> None:
        ...  # pragma: no cover
