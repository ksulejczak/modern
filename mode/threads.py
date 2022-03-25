import asyncio
import concurrent
from threading import Thread
from typing import Optional

from .service import Service


class ServiceThread(Service):
    def __init__(self) -> None:
        super().__init__()
        self._thread: Optional[Thread] = None
        self._parent_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread_started_event = asyncio.Event()

    async def _create_my_tasks(self) -> None:
        def _start() -> None:
            asyncio.run(self._run_tasks())

        self._parent_loop = asyncio.get_running_loop()
        thread = Thread(target=_start)
        thread.start()
        self._thread = thread
        print("waiting")
        await self._thread_started_event.wait()
        print("at last")

    async def _stop_running_tasks(self) -> None:
        if self._thread is not None and self._loop is not None:
            future = asyncio.run_coroutine_threadsafe(
                self._stop_loop(),
                self._loop,
            )
            while True:
                try:
                    future.result(timeout=0)
                except concurrent.futures.TimeoutError:
                    await asyncio.sleep(0.01)
                else:
                    break
            self._loop.stop()
            self._thread.join()
            self._thread = None
            self._loop = None

    async def _run_tasks(self) -> None:
        print("Running tasks")
        self._loop = asyncio.get_running_loop()
        await super()._create_my_tasks()
        print("notify")
        asyncio.run_coroutine_threadsafe(
            self._set_event(),
            self._parent_loop,
        )
        print("notified")
        print("endless loop")
        while True:
            print("sleep")
            await asyncio.sleep(0.1)

    async def _set_event(self):
        print("set event")
        self._thread_started_event.set()
        print("set done")

    async def _stop_loop(self):
        print("stopping")
        await super()._stop_running_tasks()
        print("stop loop")
        self._loop.stop()
        print("stopped")
