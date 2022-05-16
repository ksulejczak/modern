import asyncio
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from time import monotonic
from typing import AsyncGenerator, Generator

import pytest

from modern.service import Service, ServiceAlreadyRunError, ServiceNotRunError
from modern.threads import ServiceThread
from modern.types import ServiceState


@dataclass
class CallbackCounts:
    first_start: int = 0
    start: int = 0
    started: int = 0
    stop: int = 0
    shutdown: int = 0
    restart: int = 0


class ServiceStub(ServiceThread):
    def __init__(self) -> None:
        super().__init__()
        self.task1_run = 0
        self.timer1_run = 0
        self.callback_counts = CallbackCounts()

    async def on_first_start(self) -> None:
        self.callback_counts.first_start += 1

    async def on_start(self) -> None:
        self.callback_counts.start += 1

    async def on_started(self) -> None:
        self.callback_counts.started += 1

    async def on_stop(self) -> None:
        self.callback_counts.stop += 1

    async def on_shutdown(self) -> None:
        self.callback_counts.shutdown += 1

    async def on_restart(self) -> None:
        self.callback_counts.restart += 1

    @ServiceThread.task
    async def task1(self) -> None:
        await asyncio.sleep(0)
        self.task1_run += 1

    @ServiceThread.timer(interval=0.01)
    async def timer1(self) -> None:
        self.timer1_run += 1


@contextmanager
def stub_contextmanager() -> Generator[None, None, None]:
    yield None


@asynccontextmanager
async def stub_asynccontextmanager() -> AsyncGenerator[None, None]:
    yield None


@pytest.mark.asyncio
async def test_from_awaitable() -> None:
    calls: list[int] = []

    async def call() -> None:
        calls.append(1)

    service = Service.from_awaitable(call())

    assert isinstance(service, Service)
    async with service:
        pass
    assert calls == [1]


@pytest.mark.asyncio
async def test_on_first_start() -> None:
    service = ServiceStub()
    assert service.callback_counts.first_start == 0

    async with service:
        pass

    assert service.callback_counts.first_start == 1


@pytest.mark.asyncio
async def test_on_first_start_is_run_only_once() -> None:
    service = ServiceStub()
    assert service.callback_counts.first_start == 0

    async with service:
        pass
    async with service:
        pass

    assert service.callback_counts.first_start == 1


@pytest.mark.asyncio
async def test_on_first_start_is_not_run_on_restart() -> None:
    service = ServiceStub()
    assert service.callback_counts.first_start == 0

    async with service:
        pass
    for _ in range(2):
        await service.restart()

    assert service.callback_counts.first_start == 1
    await service.stop()


@pytest.mark.asyncio
async def test_on_start() -> None:
    service = ServiceStub()
    assert service.callback_counts.start == 0

    async with service:
        assert service.callback_counts.start == 1


@pytest.mark.asyncio
async def test_on_started() -> None:
    service = ServiceStub()
    assert service.callback_counts.started == 0

    async with service:
        assert service.callback_counts.started == 1


@pytest.mark.asyncio
async def test_on_stop() -> None:
    service = ServiceStub()
    await service.start()
    assert service.callback_counts.stop == 0

    await service.stop()

    assert service.callback_counts.stop == 1


@pytest.mark.asyncio
async def test_on_shutdown() -> None:
    service = ServiceStub()
    await service.start()
    assert service.callback_counts.shutdown == 0

    await service.stop()

    assert service.callback_counts.shutdown == 1


@pytest.mark.asyncio
async def test_on_restart() -> None:
    service = ServiceStub()

    await service.start()
    assert service.callback_counts.restart == 0

    await service.stop()
    assert service.callback_counts.restart == 0

    await service.restart()
    assert service.callback_counts.restart == 1

    await service.stop()


@pytest.mark.asyncio
async def test_get_state() -> None:
    service = ServiceStub()

    assert service.get_state() is ServiceState.INIT

    async with service:
        assert service.get_state() is ServiceState.RUNNING

    assert service.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_add_dependency_dependent_service_is_run_on_start() -> None:
    service = ServiceStub()
    dependency = ServiceStub()
    added_service = service.add_dependency(dependency)

    assert added_service is dependency
    assert dependency.callback_counts.started == 0

    async with service:
        assert dependency.callback_counts.started == 1
        assert dependency.get_state() is ServiceState.RUNNING

    assert service.get_state() is ServiceState.SHUTDOWN
    assert dependency.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_add_dependency_dependent_service_is_stopped_on_stop() -> None:
    service = ServiceStub()
    dependency = ServiceStub()
    added_service = service.add_dependency(dependency)
    assert added_service is dependency

    assert dependency.callback_counts.stop == 0
    async with service:
        pass

    assert dependency.callback_counts.stop == 1


@pytest.mark.asyncio
async def test_add_runtime_dependency_attach_to_not_started_service() -> None:
    service = ServiceStub()
    dependency = ServiceStub()

    added_service = await service.add_runtime_dependency(dependency)

    assert added_service is dependency
    assert dependency.callback_counts.start == 0

    async with service:
        assert dependency.callback_counts.start == 1
        assert dependency.get_state() is ServiceState.RUNNING

    assert dependency.callback_counts.stop == 1
    assert service.get_state() is ServiceState.SHUTDOWN
    assert dependency.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_add_runtime_dependency_attach_to_not_running_service() -> None:
    service = ServiceStub()
    dependency = ServiceStub()

    async with service:
        assert dependency.callback_counts.start == 0

        added_service = await service.add_runtime_dependency(dependency)

        assert added_service is dependency
        assert dependency.callback_counts.start == 1
        assert dependency.callback_counts.stop == 0
        assert dependency.get_state() is ServiceState.RUNNING

    assert dependency.callback_counts.stop == 1


@pytest.mark.asyncio
async def test_remove_dependency_existing_dependecy_is_stopped() -> None:
    service = ServiceStub()
    dependency = ServiceStub()
    service.add_dependency(dependency)

    async with service:
        assert dependency.callback_counts.stop == 0

        removed_dependency = await service.remove_dependency(dependency)

        assert removed_dependency is dependency
        assert dependency.callback_counts.stop == 1
        assert dependency.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_remove_dependency_invalid_dependency() -> None:
    service = ServiceStub()
    dependency = ServiceStub()

    with pytest.raises(ValueError):
        await service.remove_dependency(dependency)


@pytest.mark.asyncio
async def test_add_context() -> None:
    service = ServiceStub()
    what: list[str] = []

    @contextmanager
    def cm():
        what.append("started")
        yield None
        what.append("stopped")

    service.add_context(cm())
    assert what == []

    async with service:
        assert what == ["started"]

    assert what == ["started", "stopped"]


@pytest.mark.asyncio
async def test_add_async_context() -> None:
    service = ServiceStub()
    what: list[str] = []

    @asynccontextmanager
    async def cm():
        what.append("started")
        yield None
        what.append("stopped")

    await service.add_async_context(cm())
    assert what == []

    async with service:
        assert what == ["started"]

    assert what == ["started", "stopped"]


@pytest.mark.asyncio
async def test_start() -> None:
    service = ServiceStub()

    async with service:
        await asyncio.sleep(0.02)

    assert service.task1_run == 1
    assert service.timer1_run > 0


@pytest.mark.asyncio
async def test_start_on_already_started_service() -> None:
    service = ServiceStub()

    async with service:
        with pytest.raises(ServiceAlreadyRunError):
            await service.start()


@pytest.mark.asyncio
async def test_maybe_start_on_not_running_service() -> None:
    service = ServiceStub()

    started = await service.maybe_start()

    assert started is True
    await service.stop()


@pytest.mark.asyncio
async def test_maybe_start_on_running_service() -> None:
    service = ServiceStub()
    await service.start()

    started = await service.maybe_start()

    assert started is False
    await service.stop()


@pytest.mark.asyncio
async def test_crash_raises_if_not_run() -> None:
    service = ServiceStub()

    with pytest.raises(ServiceNotRunError):
        await service.crash(ValueError())

    assert service.get_state() is ServiceState.INIT


@pytest.mark.asyncio
async def test_crash_stops_all_running_tasks() -> None:
    service = ServiceStub.from_awaitable(asyncio.sleep(10))

    time0 = monotonic()
    async with service:
        await service.crash(ValueError())
    time1 = monotonic()

    assert time1 - time0 < 1


@pytest.mark.asyncio
async def test_crash_propagetes_to_children() -> None:
    service = ServiceStub()
    dependency = ServiceStub.from_awaitable(asyncio.sleep(10))
    service.add_dependency(dependency)

    time0 = monotonic()
    async with service:
        await service.crash(ValueError())
    time1 = monotonic()

    assert time1 - time0 < 1
    assert service.get_state() is ServiceState.CRASHED
    assert dependency.get_state() is ServiceState.CRASHED


@pytest.mark.asyncio
async def test_stop_on_not_started_service() -> None:
    service = ServiceStub()

    await service.stop()

    assert service.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_stop_on_started_service() -> None:
    service = ServiceStub()
    await service.start()

    await service.stop()

    assert service.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_stop_on_already_stopped_service() -> None:
    service = ServiceStub()
    await service.stop()

    await service.stop()

    assert service.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_stop_on_long_running_service_cancels_tasks() -> None:
    long_runing_service = Service.from_awaitable(asyncio.sleep(10))

    time0 = monotonic()
    async with long_runing_service:
        await long_runing_service.stop()
    time1 = monotonic()

    assert time1 - time0 < 1


def test_service_reset() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        service.service_reset()


@pytest.mark.asyncio
async def test_restart_raises_if_service_is_not_run() -> None:
    service = ServiceStub()

    with pytest.raises(ServiceNotRunError):
        await service.restart()

    await service.stop()


@pytest.mark.asyncio
async def test_restart_stops_and_restarts_tasks() -> None:
    service = ServiceStub()

    async with service:
        await asyncio.sleep(0.01)
        assert service.task1_run == 1

        await service.restart()

        assert service.callback_counts.restart == 1
        await asyncio.sleep(0.01)
        assert service.task1_run == 2
        assert service.get_state() is ServiceState.RUNNING

    assert service.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_restart_on_crashed_service() -> None:
    service = ServiceStub()
    async with service:
        await service.crash(ValueError())
    assert service.get_state() is ServiceState.CRASHED

    await service.restart()
    assert service.get_state() is ServiceState.RUNNING
    await service.stop()


@pytest.mark.asyncio
async def test_wait_until_stopped_raises_for_not_started_service() -> None:
    service = ServiceStub()

    with pytest.raises(ServiceNotRunError):
        await service.wait_until_stopped()


@pytest.mark.asyncio
async def test_wait_until_stopped_for_stopped_service() -> None:
    service = ServiceStub()
    await service.stop()

    await service.wait_until_stopped()


@pytest.mark.asyncio
async def test_wait_until_stopped_for_running_service() -> None:
    async def _stop_later():
        await asyncio.sleep(0.05)
        await service.stop()

    service = ServiceStub()
    await service.start()
    loop = asyncio.get_running_loop()
    loop.create_task(_stop_later())

    time0 = monotonic()
    await service.wait_until_stopped()
    time1 = monotonic()

    assert time1 - time0 > 0.05


def test_set_shutdown() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        service.set_shutdown()


@pytest.mark.asyncio
async def test_service_as_context_manager() -> None:
    service = ServiceStub()

    async with service as context_service:
        assert context_service is service

    assert service.callback_counts.first_start == 1
    assert service.callback_counts.start == 1
    assert service.callback_counts.stop == 1
    assert service.callback_counts.start == 1
