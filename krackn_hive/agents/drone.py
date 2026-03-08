from __future__ import annotations

from .base import Agent


class DroneAgent(Agent):
    async def run(self) -> None:
        while not self.stopped():
            break
