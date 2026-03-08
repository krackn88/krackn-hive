from __future__ import annotations

from .base import Agent


class GuardAgent(Agent):
    async def run(self) -> None:
        while not self.stopped():
            break
