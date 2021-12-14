from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any

from .types import ServiceT


class ServiceWithCallbacks(ServiceT):
    async def on_first_start(self) -> None:
        pass  # pragma: no cover

    async def on_start(self) -> None:
        pass  # pragma: no cover

    async def on_started(self) -> None:
        pass  # pragma: no cover

    async def on_stop(self) -> None:
        pass  # pragma: no cover

    async def on_shutdown(self) -> None:
        pass  # pragma: no cover

    async def on_restart(self) -> None:
        pass  # pragma: no cover


class Service(ServiceWithCallbacks):
    def add_dependency(self, service: ServiceT) -> ServiceT:
        raise NotImplementedError(self)

    async def add_runtime_dependency(self, service: ServiceT) -> ServiceT:
        raise NotImplementedError(self)

    async def remove_dependency(self, service: ServiceT) -> ServiceT:
        raise NotImplementedError(self)

    def add_context(self, context: AbstractContextManager) -> Any:
        raise NotImplementedError(self)

    async def add_async_context(
        self,
        context: AbstractAsyncContextManager,
    ) -> Any:
        raise NotImplementedError(self)

    async def start(self) -> None:
        raise NotImplementedError(self)

    async def maybe_start(self) -> bool:
        raise NotImplementedError(self)

    async def crash(self, reason: BaseException) -> None:
        raise NotImplementedError(self)

    async def stop(self) -> None:
        raise NotImplementedError(self)

    def service_reset(self) -> None:
        raise NotImplementedError(self)

    async def restart(self) -> None:
        raise NotImplementedError(self)

    async def wait_until_stopped(self) -> None:
        raise NotImplementedError(self)

    def set_shutdown(self) -> None:
        raise NotImplementedError(self)
