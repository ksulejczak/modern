from __future__ import annotations

import asyncio
import enum
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from functools import wraps
from typing import Any, Awaitable, Callable, Type

from .types import ServiceT


class ServiceState(enum.Enum):
    INIT = "init"
    RUNNING = "running"
    STOPPING = "stopping"
    CRASHED = "crashed"
    SHUTDOWN = "shutdown"


class ServiceError(Exception):
    pass


class ServiceAlreadyRunError(ServiceError):
    pass


class ServiceNotRunError(ServiceError):
    pass


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
    @classmethod
    def from_awaitable(cls: Type[Service], coro: Awaitable[Any]) -> Service:
        class _SericeFromAwaitable(cls):  # type: ignore
            @Service.task
            async def task(self) -> None:
                await coro

        return _SericeFromAwaitable()

    def __init__(self) -> None:
        self._state = ServiceState.INIT
        self._restart_count = 0
        self._should_stop = False
        self._tasks: list[asyncio.Task] = []
        self._stopped = asyncio.Event()

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
        if self._state is not ServiceState.INIT:
            raise ServiceAlreadyRunError(self._state)
        await self.on_start()
        for task in self._collect_tasks():
            async_task = asyncio.create_task(task(self))
            self._tasks.append(async_task)
        self._state = ServiceState.RUNNING
        await self.on_started()

    async def maybe_start(self) -> bool:
        if self._state is ServiceState.INIT:
            await self.start()
            return True
        else:
            return False

    async def crash(self, reason: BaseException) -> None:
        raise NotImplementedError(self)

    async def stop(self) -> None:
        if self._stopped.is_set():
            return
        self._state = ServiceState.STOPPING
        await self.on_stop()
        self._should_stop = True
        running_tasks = [task for task in self._tasks if not task.done()]
        if running_tasks:
            await asyncio.wait(
                running_tasks,
                return_when=asyncio.ALL_COMPLETED,
                timeout=0,
            )
            for task in running_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.wait(
                running_tasks,
                return_when=asyncio.ALL_COMPLETED,
                timeout=None,
            )
        self._stopped.set()
        await self.on_shutdown()

    def service_reset(self) -> None:
        raise NotImplementedError(self)

    async def restart(self) -> None:
        raise NotImplementedError(self)

    async def wait_until_stopped(self) -> None:
        if self._stopped.is_set():
            return
        if self._state is not ServiceState.RUNNING:
            raise ServiceNotRunError(self._state)
        await self._stopped.wait()

    def set_shutdown(self) -> None:
        raise NotImplementedError(self)

    @classmethod
    def task(cls, fun: _Task) -> _Task:
        fun._mode_task = True  # type: ignore
        return fun

    @classmethod
    def timer(cls, interval: float) -> Callable[[_Task], _Task]:
        def _decorate(fun: _Task) -> _Task:
            fun._mode_timer = interval  # type: ignore
            return fun

        return _decorate

    def _make_timer_task(self, fun: _Task, interval: float) -> _Task:
        @wraps(fun)
        async def _timer(self: Service) -> None:
            while self._should_stop is False:
                await asyncio.sleep(interval)
                if not self._should_stop:
                    await fun(self)

        return _timer

    def _collect_tasks(self):
        for klass in self.__class__.__mro__:
            if not issubclass(klass, Service):
                continue
            for attr_value in klass.__dict__.values():
                if getattr(attr_value, "_mode_task", False) is True:
                    yield attr_value
                seconds = getattr(attr_value, "_mode_timer", None)
                if seconds is not None:
                    yield self._make_timer_task(attr_value, seconds)


_Task = Callable[[Any], Awaitable[None]]
