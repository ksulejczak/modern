import asyncio
from contextlib import asynccontextmanager, contextmanager
from time import monotonic
from typing import AsyncGenerator, Generator

import pytest

from mode.service import Service, ServiceAlreadyRunError, ServiceNotRunError

pytestmark = [pytest.mark.asyncio]


class ServiceStub(Service):
    def __init__(self) -> None:
        super().__init__()
        self.task1_run = 0
        self.timer1_run = 0

    async def on_first_start(self) -> None:
        raise NotImplementedError(self)

    async def on_start(self) -> None:
        raise NotImplementedError(self)

    async def on_started(self) -> None:
        raise NotImplementedError(self)

    async def on_stop(self) -> None:
        raise NotImplementedError(self)

    async def on_shutdown(self) -> None:
        raise NotImplementedError(self)

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


async def test_on_start() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.on_start()


async def test_on_started() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.on_started()


async def test_on_stop() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.on_stop()


async def test_on_shutdown() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.on_shutdown()


async def test_on_restart() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.on_restart()


def test_add_dependency() -> None:
    service = ServiceStub()
    dependency = ServiceStub()

    with pytest.raises(NotImplementedError):
        service.add_dependency(dependency)


async def test_add_runtime_dependency() -> None:
    service = ServiceStub()
    dependency = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.add_runtime_dependency(dependency)


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


async def test_maybe_start() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.maybe_start()


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
