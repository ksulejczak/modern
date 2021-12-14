from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

import pytest

from mode.service import Service

pytestmark = [pytest.mark.asyncio]


class ServiceStub(Service):
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


@contextmanager
def stub_contextmanager() -> Generator[None, None, None]:
    yield None


@asynccontextmanager
async def stub_asynccontextmanager() -> AsyncGenerator[None, None]:
    yield None


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

    with pytest.raises(NotImplementedError):
        await service.start()


async def test_maybe_start() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.maybe_start()


async def test_crash() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.crash(ValueError())


async def test_stop() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.stop()


def test_service_reset() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        service.service_reset()


async def test_restart() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.restart()


async def test_wait_until_stopped() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        await service.wait_until_stopped()


def test_set_shutdown() -> None:
    service = ServiceStub()

    with pytest.raises(NotImplementedError):
        service.set_shutdown()
