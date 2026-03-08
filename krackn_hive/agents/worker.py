from __future__ import annotations

from .base import Agent


class WorkerAgent(Agent):
    async def run(self) -> None:
        while not self.stopped():
            break
