import asyncio
from time import monotonic

from modern import ServiceState, ServiceT


async def active_wait_for_service_state(
    service: ServiceT,
    desired_state: ServiceState,
    timeout: float,
) -> bool:
    wait_till = monotonic() + timeout
    while True:
        state = service.get_state()
        if state is desired_state:
            return True
        if monotonic() > wait_till:
            return False
        await asyncio.sleep(0.01)
