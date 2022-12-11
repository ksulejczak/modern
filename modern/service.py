from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
    ExitStack,
)
from functools import wraps
from types import TracebackType
from typing import Any

from .types import ServiceState, ServiceT

log = logging.getLogger(__name__)


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
    def from_awaitable(cls: type[Service], coro: _Task) -> Service:
        service = cls()
        service.add_task(coro)
        return service

    def __init__(self) -> None:
        self._state = ServiceState.INIT
        self._start_count = 0
        self._should_stop = False
        self._tasks_to_start: list[_Task] = []
        self._tasks: list[asyncio.Task] = []
        self._children: list[ServiceT] = []
        self._stopped = asyncio.Event()
        self._async_exit_stack: AsyncExitStack | None = None
        self._async_context_managers: list[AbstractAsyncContextManager] = []
        self._exit_stack: ExitStack | None = None
        self._context_managers: list[AbstractContextManager] = []
        self._crash_reason: BaseException | None = None

    def get_state(self) -> ServiceState:
        return self._state

    def get_crash_reason(self) -> BaseException | None:
        return self._crash_reason

    def add_dependency(self, service: ServiceT) -> ServiceT:
        self._children.append(service)
        return service

    async def add_runtime_dependency(self, service: ServiceT) -> ServiceT:
        self.add_dependency(service)
        if self._state is ServiceState.RUNNING:
            await service.maybe_start()
        return service

    async def remove_dependency(self, service: ServiceT) -> ServiceT:
        self._children.remove(service)
        await service.stop()
        return service

    def add_context(self, context: AbstractContextManager) -> None:
        self._context_managers.append(context)

    async def add_async_context(
        self,
        context: AbstractAsyncContextManager,
    ) -> None:
        self._async_context_managers.append(context)

    async def start(self) -> None:
        if self._state not in _STATES_INACTIVE:
            raise ServiceAlreadyRunError(self._state)
        self._state = ServiceState.STARTING
        self._stopped.clear()
        if self._start_count == 0:
            await self.on_first_start()
        await self.on_start()

        if self._children:
            await asyncio.gather(
                *(child.maybe_start() for child in self._children)
            )

        if self._async_context_managers:
            async_exit_stack = self._async_exit_stack = AsyncExitStack()
            for async_context_manager in self._async_context_managers:
                await async_exit_stack.enter_async_context(
                    async_context_manager
                )
            await async_exit_stack.__aenter__()
            self._async_context_managers.clear()

        if self._context_managers:
            exit_stack = self._exit_stack = ExitStack()
            for context_manager in self._context_managers:
                exit_stack.enter_context(context_manager)
            exit_stack.__enter__()
            self._context_managers.clear()

        await self._create_my_tasks()

        self._state = ServiceState.RUNNING
        await self.on_started()
        self._start_count += 1

    async def maybe_start(self) -> bool:
        if self._state is ServiceState.INIT:
            await self.start()
            return True
        else:
            return False

    async def crash(self, reason: BaseException) -> None:
        if self._state not in _STATES_ACTIVE:
            raise ServiceNotRunError(self._state)
        self._should_stop = True
        await self._stop_running_tasks()
        self._stopped.set()
        for child in self._children:
            await child.crash(reason)
        self._crash_reason = reason
        self._state = ServiceState.CRASHED

    async def stop(self) -> None:
        if self._stopped.is_set():
            return
        await self._do_shutdown()

    def service_reset(self) -> None:
        raise NotImplementedError(self)

    async def restart(self) -> None:
        if self._state not in _STATES_RESTARTABLE:
            raise ServiceNotRunError(self._state)
        await self._do_shutdown()
        await self.on_restart()
        await self.start()

    async def wait_until_stopped(self) -> None:
        if self._stopped.is_set():
            return
        if self._state is not ServiceState.RUNNING:
            raise ServiceNotRunError(self._state)
        await self._stopped.wait()

    def set_shutdown(self) -> None:
        raise NotImplementedError(self)

    async def __aenter__(self) -> Service:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        await self.stop()

    def add_task(self, func: _Task) -> None:
        if self._state is not ServiceState.INIT:
            raise ServiceAlreadyRunError(self._state)

        self._tasks_to_start.append(func)

    def add_timer_task(self, func: _Task, interval: float) -> None:
        @wraps(func)
        async def _timer() -> None:
            while self._should_stop is False:
                await asyncio.sleep(interval)
                if not self._should_stop:
                    await func()

        self.add_task(_timer)

    async def _create_my_tasks(self) -> None:
        def make_guarded_task(func: _Task) -> _Task:
            async def _task() -> None:
                for fail in range(10):
                    try:
                        await func()
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        log.exception(
                            "Task %s failed %s/10.", func.__name__, fail + 1
                        )
                        reason = e
                    else:
                        break
                else:
                    log.error(
                        "Task %s failed too many times. Stopping service.",
                        func.__name__,
                    )
                    asyncio.create_task(self.crash(reason))

            return _task

        for task in self._tasks_to_start:
            async_task = asyncio.create_task(make_guarded_task(task)())
            self._tasks.append(async_task)

    def _reset(self) -> None:
        self._should_stop = False
        self._tasks.clear()
        self._children.clear()
        self._async_exit_stack = None
        self._async_context_managers.clear()
        self._exit_stack = None
        self._context_managers.clear()
        self._crash_reason = None

    async def _stop_running_tasks(self) -> None:
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

    async def _do_shutdown(self) -> None:
        self._state = ServiceState.STOPPING
        await self.on_stop()
        self._should_stop = True

        if self._children:
            await asyncio.gather(*(child.stop() for child in self._children))

        if self._async_exit_stack:
            await self._async_exit_stack.__aexit__(None, None, None)

        if self._exit_stack:
            self._exit_stack.__exit__(None, None, None)

        await self._stop_running_tasks()

        self._stopped.set()
        self._state = ServiceState.SHUTDOWN
        await self.on_shutdown()
        self._reset()


_Task = Callable[[], Coroutine[Any, Any, None]]
_STATES_ACTIVE = frozenset({ServiceState.RUNNING, ServiceState.STOPPING})
_STATES_INACTIVE = frozenset({ServiceState.INIT, ServiceState.SHUTDOWN})
_STATES_RESTARTABLE = frozenset(
    {ServiceState.RUNNING, ServiceState.CRASHED, ServiceState.SHUTDOWN}
)
