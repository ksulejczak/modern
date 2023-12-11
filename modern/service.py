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
from time import monotonic
from types import TracebackType
from typing import Any, Final

from .types import ServiceState, ServiceT

log = logging.getLogger(__name__)
DEFAULT_CHILDREN_WATCH_INTERVAL: Final[float] = 1.0


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
    def from_awaitable(
        cls: type[Service],
        coro: _Task,
        children_watch_interval: float = DEFAULT_CHILDREN_WATCH_INTERVAL,
    ) -> Service:
        service = cls(children_watch_interval=children_watch_interval)
        service.add_task(coro)
        return service

    def __init__(
        self,
        children_watch_interval: float = DEFAULT_CHILDREN_WATCH_INTERVAL,
        level: int = 0,
        name: str | None = None,
    ) -> None:
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
        self._children_watch_interval = children_watch_interval
        self._name = name or self.__class__.__name__
        self.set_level(level)

    def get_state(self) -> ServiceState:
        return self._state

    def get_name(self) -> str:
        return self._name

    def get_level(self) -> int:
        return self._level

    def set_level(self, level: int) -> None:
        self._level = level
        self._log_lead = f'{"--" * level}> {self._name}:'
        for child in self._children:
            child.set_level(level + 1)

    def get_crash_reason(self) -> BaseException | None:
        return self._crash_reason

    def add_dependency(self, service: ServiceT) -> ServiceT:
        service.set_level(self._level + 1)
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
        self._log_debug("Starting service")
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
        self._log_info("Crashing service with reason %s", reason)
        if self._state not in _STATES_ACTIVE:
            raise ServiceNotRunError(self._state)
        self._should_stop = True
        await self._stop_running_tasks()
        self._stopped.set()
        self._log_info("crashing children")
        for child in self._children:
            if child.get_state() in _STATES_ACTIVE:
                await child.crash(reason)
        self._crash_reason = reason
        self._state = ServiceState.CRASHED

    async def stop(self) -> None:
        if self._stopped.is_set():
            return
        self._log_debug("Stopping service")
        await self._do_shutdown()

    def service_reset(self) -> None:
        raise NotImplementedError(self)

    async def restart(self) -> None:
        if self._state not in _STATES_RESTARTABLE:
            raise ServiceNotRunError(self._state)
        self._log_debug("Restarting service")
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
        self.add_task(self._make_timer_task(func, interval))

    async def _create_my_tasks(self) -> None:
        for task in self._tasks_to_start:
            async_task = asyncio.create_task(self._make_guarded_task(task)())
            self._tasks.append(async_task)

        self._tasks.append(
            asyncio.create_task(
                self._make_timer_task(
                    self._watch_children,
                    interval=self._children_watch_interval,
                )()
            )
        )

    def _make_guarded_task(self, func: _Task) -> _Task:
        async def _task() -> None:
            for fail in range(10):
                self._log_warning("time: %s", monotonic())
                try:
                    await func()
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self._log_exception(
                        "Task %s failed %s/10.", func.__name__, fail + 1
                    )
                    reason = e
                else:
                    break
            else:
                self._log_error(
                    "Task %s failed too many times. Stopping service.",
                    func.__name__,
                )
                asyncio.create_task(self.crash(reason))

        return _task

    async def _watch_children(self) -> None:
        my_state = self.get_state()
        if my_state is not ServiceState.RUNNING:  # pragma: no cover
            return
        for child in self._children:
            if child.get_state() is ServiceState.CRASHED:
                # we cannot just call self.crash() here as this will cancel
                # this very method and crash() as itself
                self._log_warning(
                    "Child %s crashed! We will crash as well!",
                    child.get_name(),
                )
                self._schedule_crash(child.get_crash_reason())

    def _schedule_crash(self, reason: BaseException | None) -> None:
        asyncio.get_running_loop().create_task(
            self.crash(reason or RuntimeError("Crash from child"))
        )

    def _make_timer_task(self, func: _Task, interval: float) -> _Task:
        @wraps(func)
        async def _timer() -> None:
            while self._should_stop is False:
                should_wake_at = monotonic() + interval
                await asyncio.sleep(interval)
                now = monotonic()
                diff = now - should_wake_at
                if abs(diff) > 0.1:
                    self._log_warning(
                        "Task %s time drift: %ss",
                        func.__name__,
                        diff,
                    )
                if not self._should_stop:
                    await func()

        return _timer

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

    def _log_debug(self, msg: str, *args: Any) -> None:
        return log.debug(f"{self._log_lead} {msg}", *args)

    def _log_info(self, msg: str, *args: Any) -> None:
        return log.info(f"{self._log_lead} {msg}", *args)

    def _log_warning(self, msg: str, *args: Any) -> None:
        return log.warning(f"{self._log_lead} {msg}", *args)

    def _log_error(self, msg: str, *args: Any) -> None:
        return log.error(f"{self._log_lead} {msg}", *args)

    def _log_exception(self, msg: str, *args: Any) -> None:
        return log.exception(f"{self._log_lead} {msg}", *args)


_Task = Callable[[], Coroutine[Any, Any, None]]
_STATES_ACTIVE = frozenset({ServiceState.RUNNING, ServiceState.STOPPING})
_STATES_INACTIVE = frozenset({ServiceState.INIT, ServiceState.SHUTDOWN})
_STATES_RESTARTABLE = frozenset(
    {ServiceState.RUNNING, ServiceState.CRASHED, ServiceState.SHUTDOWN}
)
