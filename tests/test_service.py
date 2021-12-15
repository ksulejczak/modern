import asyncio
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from time import monotonic
from typing import AsyncGenerator, Generator

import pytest

from mode.service import Service, ServiceAlreadyRunError, ServiceNotRunError

pytestmark = [pytest.mark.asyncio]


@dataclass
class CallbackCounts:
    first_start: int = 0
    start: int = 0
    started: int = 0
    stop: int = 0
    shutdown: int = 0
    restart: int = 0


class ServiceStub(Service):
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
        raise NotImplementedError(self)

    @Service.task
    async def task1(self) -> None:
        await asyncio.sleep(0)
        self.task1_run += 1

    @Service.timer(interval=0.01)
    async def timer1(self) -> None:
        self.timer1_run += 1


@contextmanager
def stub_contextmanager() -> Generator[None, None, None]:
    yield None


@asynccontextmanager
async def stub_asynccontextmanager() -> AsyncGenerator[None, None]:
    yield None


async def test_from_awaitable() -> None:
    calls: list[int] = []

    async def call() -> None:
        calls.append(1)

    service = Service.from_awaitable(call())

    assert isinstance(service, Service)
    await service.start()
    await service.stop()
    assert calls == [1]


async def test_on_first_start() -> None:
    service = ServiceStub()
    assert service.callback_counts.first_start == 0

    await service.start()

    assert service.callback_counts.first_start == 1
    await service.stop()


async def test_on_start() -> None:
    service = ServiceStub()
    assert service.callback_counts.start == 0

    await service.start()

    assert service.callback_counts.start == 1


async def test_on_started() -> None:
    service = ServiceStub()
    assert service.callback_counts.started == 0

    await service.start()

    assert service.callback_counts.started == 1


async def test_on_stop() -> None:
    service = ServiceStub()
    await service.start()
    assert service.callback_counts.stop == 0

    await service.stop()

    assert service.callback_counts.stop == 1


async def test_on_shutdown() -> None:
    service = ServiceStub()
    await service.start()
    assert service.callback_counts.shutdown == 0

    await service.stop()

    assert service.callback_counts.shutdown == 1


async def test_on_restart() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.on_restart()


async def test_add_dependency_dependent_service_is_run_on_start() -> None:
    service = ServiceStub()
    dependency = ServiceStub()
    added_service = service.add_dependency(dependency)

    assert added_service is dependency
    assert dependency.callback_counts.started == 0

    await service.start()

    assert dependency.callback_counts.started == 1
    await service.stop()


async def test_add_dependency_dependent_service_is_stopped_on_stop() -> None:
    service = ServiceStub()
    dependency = ServiceStub()
    added_service = service.add_dependency(dependency)
    assert added_service is dependency
    await service.start()
    assert dependency.callback_counts.stop == 0

    await service.stop()

    assert dependency.callback_counts.stop == 1


async def test_add_runtime_dependency_attach_to_not_started_service() -> None:
    service = ServiceStub()
    dependency = ServiceStub()

    added_service = await service.add_runtime_dependency(dependency)

    assert added_service is dependency
    assert dependency.callback_counts.start == 0

    await service.start()

    assert dependency.callback_counts.start == 1

    await service.stop()
    assert dependency.callback_counts.stop == 1


async def test_add_runtime_dependency_attach_to_not_running_service() -> None:
    service = ServiceStub()
    dependency = ServiceStub()
    await service.start()
    assert dependency.callback_counts.start == 0

    added_service = await service.add_runtime_dependency(dependency)

    assert added_service is dependency
    assert dependency.callback_counts.start == 1

    await service.stop()
    assert dependency.callback_counts.stop == 1


async def test_remove_dependency() -> None:
    service = ServiceStub()
    dependency = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.remove_dependency(dependency)


def test_add_context() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        service.add_context(stub_contextmanager())


async def test_add_async_context() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.add_async_context(stub_asynccontextmanager())


async def test_start() -> None:
    service = ServiceStub()

    await service.start()
    await asyncio.sleep(0.02)

    assert service.task1_run == 1
    assert service.timer1_run > 0


async def test_start_on_already_started_service() -> None:
    service = ServiceStub()
    await service.start()

    with pytest.raises(ServiceAlreadyRunError):
        await service.start()


async def test_maybe_start_on_not_running_service() -> None:
    service = ServiceStub()

    started = await service.maybe_start()

    assert started is True
    await service.stop()


async def test_maybe_start_on_running_service() -> None:
    service = ServiceStub()
    await service.start()

    started = await service.maybe_start()

    assert started is False
    await service.stop()


async def test_crash() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.crash(ValueError())


async def test_stop_on_not_started_service() -> None:
    service = ServiceStub()

    await service.stop()


async def test_stop_on_started_service() -> None:
    service = ServiceStub()
    await service.start()

    await service.stop()


async def test_stop_on_already_stopped_service() -> None:
    service = ServiceStub()
    await service.stop()

    await service.stop()


async def test_stop_on_long_running_service_cancels_tasks() -> None:
    long_runing_service = Service.from_awaitable(asyncio.sleep(10))
    await long_runing_service.start()

    time0 = monotonic()
    await long_runing_service.stop()
    time1 = monotonic()

    assert time1 - time0 < 1


def test_service_reset() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        service.service_reset()


async def test_restart() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.restart()


async def test_wait_until_stopped_raises_for_not_started_service() -> None:
    service = ServiceStub()

    with pytest.raises(ServiceNotRunError):
        await service.wait_until_stopped()


async def test_wait_until_stopped_for_stopped_service() -> None:
    service = ServiceStub()
    await service.stop()

    await service.wait_until_stopped()


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
