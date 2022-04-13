import asyncio
from dataclasses import dataclass
from threading import Thread

from .service import Service


@dataclass(frozen=True, slots=True)
class ThreadEvents:
    parent_tasks_started: asyncio.Event
    parent_tasks_stopped: asyncio.Event
    child_tasks_stopped: asyncio.Event


class ServiceThread(Service):
    def __init__(self) -> None:
        super().__init__()
        self._thread: Thread | None = None
        self._parent_loop: asyncio.AbstractEventLoop | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._events: ThreadEvents | None = None

    async def _create_my_tasks(self) -> None:
        # this method is supposed to run in parent loop
        def _start() -> None:
            asyncio.run(self._run_tasks())

        self._parent_loop = asyncio.get_running_loop()
        self._events = ThreadEvents(
            parent_tasks_started=asyncio.Event(),
            parent_tasks_stopped=asyncio.Event(),
            child_tasks_stopped=asyncio.Event(),
        )
        thread = Thread(target=_start)
        thread.start()
        self._thread = thread
        await self._events.parent_tasks_started.wait()

    async def _stop_running_tasks(self) -> None:
        # this method is supposed to run in parent loop
        if self._events is not None and self._loop is not None:
            asyncio.run_coroutine_threadsafe(
                self._stop_tasks_from_child_thread(),
                self._loop,
            )
            await self._events.parent_tasks_stopped.wait()
            self._thread = None
            self._loop = None
            self._parent_loop = None
            self._events = None

    async def _run_tasks(self) -> None:
        # this method is supposed to run in child loop
        if self._events is not None and self._parent_loop is not None:
            self._loop = asyncio.get_running_loop()
            await super()._create_my_tasks()
            self._parent_loop.call_soon_threadsafe(
                self._events.parent_tasks_started.set
            )
            await self._events.child_tasks_stopped.wait()

    async def _stop_tasks_from_child_thread(self):
        # this method is supposed to run in child thread
        await super()._stop_running_tasks()
        self._events.child_tasks_stopped.set()
        self._parent_loop.call_soon_threadsafe(
            self._events.parent_tasks_stopped.set
        )
