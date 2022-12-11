import asyncio
from dataclasses import dataclass
from threading import Thread

from .service import (
    DEFAULT_CHILDREN_WATCH_INTERVAL,
    Service,
    ServiceNotRunError,
)


@dataclass(frozen=True, slots=True)
class ThreadData:
    thread: Thread
    parent_tasks_started: asyncio.Event
    child_tasks_stopped: asyncio.Event
    parent_loop: asyncio.AbstractEventLoop


class ServiceThread(Service):
    def __init__(
        self,
        children_watch_interval: float = DEFAULT_CHILDREN_WATCH_INTERVAL,
    ) -> None:
        super().__init__(children_watch_interval=children_watch_interval)
        self._thread_data: ThreadData | None = None
        self._thread_loop: asyncio.AbstractEventLoop | None = None

    async def crash(self, reason: BaseException) -> None:
        # this method may be called from either parent or current thread loop
        if self._thread_data is None:
            raise ServiceNotRunError(self._state)
        current_loop = asyncio.get_running_loop()
        parent_loop = self._thread_data.parent_loop
        if current_loop is parent_loop:
            await super().crash(reason)
        else:
            asyncio.run_coroutine_threadsafe(
                super().crash(reason),
                parent_loop,
            )

    async def stop(self) -> None:
        # this method may be called from either parent or current thread loop
        if self._thread_data is None:
            await super().stop()
        elif asyncio.get_running_loop() is (
            parent_loop := self._thread_data.parent_loop
        ):
            await super().stop()
        else:
            asyncio.run_coroutine_threadsafe(
                self.stop(),
                parent_loop,
            )

    async def _create_my_tasks(self) -> None:
        # this method is supposed to run in parent loop
        def _start() -> None:
            asyncio.run(self._run_tasks())

        thread = Thread(target=_start)
        self._thread_data = ThreadData(
            thread=thread,
            parent_tasks_started=asyncio.Event(),
            child_tasks_stopped=asyncio.Event(),
            parent_loop=asyncio.get_running_loop(),
        )
        thread.start()
        await self._thread_data.parent_tasks_started.wait()

    async def _stop_running_tasks(self) -> None:
        # this method is supposed to run in parent loop
        if self._thread_loop is not None:
            fut = asyncio.run_coroutine_threadsafe(
                self._stop_tasks_from_child_thread(),
                self._thread_loop,
            )
            await asyncio.get_running_loop().run_in_executor(None, fut.result)
            self._thread_data = None
            self._thread_loop = None

    async def _run_tasks(self) -> None:
        # this method is supposed to run in child loop
        if self._thread_data is not None:
            self._thread_loop = asyncio.get_running_loop()
            await super()._create_my_tasks()
            self._thread_data.parent_loop.call_soon_threadsafe(
                self._thread_data.parent_tasks_started.set
            )
            await self._thread_data.child_tasks_stopped.wait()

    async def _stop_tasks_from_child_thread(self) -> None:
        # this method is supposed to run in child thread
        await super()._stop_running_tasks()
        if self._thread_data is not None:
            self._thread_data.child_tasks_stopped.set()
