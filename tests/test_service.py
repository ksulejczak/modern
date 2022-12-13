import asyncio
import logging
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from time import monotonic, sleep

import pytest

from modern.service import (
    DEFAULT_CHILDREN_WATCH_INTERVAL,
    Service,
    ServiceAlreadyRunError,
    ServiceNotRunError,
    log,
)
from modern.types import ServiceState
from tests.tools.services import active_wait_for_service_state


@dataclass
class CallbackCounts:
    first_start: int = 0
    start: int = 0
    started: int = 0
    stop: int = 0
    shutdown: int = 0
    restart: int = 0


class ServiceStub(Service):
    def __init__(
        self, children_watch_interval: float = DEFAULT_CHILDREN_WATCH_INTERVAL
    ) -> None:
        super().__init__(children_watch_interval=children_watch_interval)
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

    service = Service.from_awaitable(call)

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


@pytest.mark.asyncio
async def test_get_state() -> None:
    service = ServiceStub()

    assert service.get_state() is ServiceState.INIT

    async with service:
        assert service.get_state() is ServiceState.RUNNING

    assert service.get_state() is ServiceState.SHUTDOWN


@pytest.mark.asyncio
async def test_get_set_level() -> None:
    service = ServiceStub()

    service.set_level(10)
    level = service.get_level()

    assert level == 10


@pytest.mark.asyncio
async def test_set_level_propagates_to_children() -> None:
    service = ServiceStub()
    dependency = ServiceStub()
    service.add_dependency(dependency)

    service.set_level(10)

    assert dependency.get_level() == 11


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
    def cm() -> Generator[None, None, None]:
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
    async def cm() -> AsyncGenerator[None, None]:
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
    counts = _add_tasks_to_service(service)

    async with service:
        await asyncio.sleep(0.02)

    assert counts.task1_run == 1
    assert counts.timer1_run > 0


@pytest.mark.asyncio
async def test_start_on_already_started_service() -> None:
    service = ServiceStub()
    await service.start()

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
    service = ServiceStub.from_awaitable(_long_running_task)

    time0 = monotonic()
    async with service:
        await service.crash(ValueError())
    time1 = monotonic()

    assert time1 - time0 < 1


@pytest.mark.asyncio
async def test_crash_propagetes_to_children() -> None:
    service = ServiceStub()
    dependency = ServiceStub.from_awaitable(_long_running_task)
    service.add_dependency(dependency)

    time0 = monotonic()
    async with service:
        await service.crash(ValueError())
    time1 = monotonic()

    assert time1 - time0 < 1
    assert service.get_state() is ServiceState.CRASHED
    assert dependency.get_state() is ServiceState.CRASHED


@pytest.mark.asyncio
async def test_crash_from_child_propagates_to_parent() -> None:
    service = ServiceStub.from_awaitable(
        _long_running_task,
        children_watch_interval=0.1,
    )
    dependency = ServiceStub()
    service.add_dependency(dependency)

    async with service:
        await dependency.crash(ValueError())
        await active_wait_for_service_state(service, ServiceState.CRASHED, 1.1)

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
    long_runing_service = Service.from_awaitable(_long_running_task)

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


@pytest.mark.asyncio
async def test_restart_stops_and_restarts_tasks() -> None:
    service = ServiceStub()
    counts = _add_tasks_to_service(service)

    async with service:
        await asyncio.sleep(0.01)
        assert counts.task1_run == 1

        await service.restart()

        assert service.callback_counts.restart == 1
        await asyncio.sleep(0.01)
        assert counts.task1_run == 2
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


@pytest.mark.asyncio
async def test_task_is_run_10_times_and_crashes_service() -> None:
    counts = TaskCounts(task1_run=0, timer1_run=0)

    async def _fail() -> None:
        counts.task1_run += 1
        raise ValueError()

    service = ServiceStub()
    service.add_task(_fail)

    async with service:
        await asyncio.sleep(0.01)

        assert service.get_state() is ServiceState.CRASHED
        assert isinstance(service.get_crash_reason(), ValueError)
        assert counts.task1_run == 10


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
    async def _stop_later() -> None:
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


@pytest.mark.asyncio
async def test_add_task_raises_if_service_is_running() -> None:
    service = ServiceStub()

    async with service:
        with pytest.raises(ServiceAlreadyRunError):
            service.add_task(_long_running_task)


@pytest.mark.asyncio
async def test_add_timer_task_raises_if_service_is_running() -> None:
    service = ServiceStub()

    async with service:
        with pytest.raises(ServiceAlreadyRunError):
            service.add_timer_task(_long_running_task, 1.0)


@pytest.mark.asyncio
async def test_timer_task_warns_about_time_drift() -> None:
    service = ServiceStub()
    _add_tasks_to_service(service)

    with _monitor_log(log) as logs:
        async with service:
            await asyncio.sleep(0)  # let the timer kick in
            sleep(0.15)  # this will block thread event loop
            await asyncio.sleep(0)  # let the handler log message

    assert any("time drift:" in log.message for log in logs)


@dataclass(slots=True)
class TaskCounts:
    task1_run: int
    timer1_run: int


def _add_tasks_to_service(service: Service) -> TaskCounts:
    counts = TaskCounts(task1_run=0, timer1_run=0)

    async def task1() -> None:
        await asyncio.sleep(0)
        counts.task1_run += 1

    async def timer1() -> None:
        counts.timer1_run += 1

    service.add_task(task1)
    service.add_timer_task(timer1, 0.01)
    return counts


async def _long_running_task() -> None:
    await asyncio.sleep(10)


@contextmanager
def _monitor_log(
    logger: logging.Logger,
) -> Generator[list[logging.LogRecord], None, None]:
    def monitor_filter(record: logging.LogRecord) -> int:
        records.append(record)
        return 1

    records: list[logging.LogRecord] = []
    logger.addFilter(monitor_filter)
    try:
        yield records
    finally:
        logger.removeFilter(monitor_filter)
