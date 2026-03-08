from __future__ import annotations

import asyncio

from ..event_bus import EventBus
from ..models import AgentState
from ..storage import CombRepository


class Agent:
    def __init__(self, agent_id: str, repository: CombRepository, bus: EventBus):
        self.agent_id = agent_id
        self.repository = repository
        self.bus = bus
        self._stop = asyncio.Event()

    async def stop(self) -> None:
        self._stop.set()

    def stopped(self) -> bool:
        return self._stop.is_set()

    async def run(self) -> None:  # pragma: no cover
        raise NotImplementedError
