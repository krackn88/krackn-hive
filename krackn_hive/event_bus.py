from __future__ import annotations

import asyncio
import fnmatch
import json
from dataclasses import dataclass
from typing import AsyncIterator, Protocol

try:
    from redis.asyncio import Redis
except ModuleNotFoundError:  # optional at test-time
    Redis = object  # type: ignore[assignment]

from .schemas import CloudEvent


class EventBus(Protocol):
    async def publish(self, event: CloudEvent) -> None: ...
    async def subscribe(self, pattern: str) -> AsyncIterator[CloudEvent]: ...


@dataclass(frozen=True)
class Subscription:
    pattern: str
    queue: asyncio.Queue[CloudEvent]


class InMemoryEventBus:
    def __init__(self) -> None:
        self._subs: list[Subscription] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: CloudEvent) -> None:
        async with self._lock:
            subs = list(self._subs)
        for sub in subs:
            if fnmatch.fnmatch(event.type, sub.pattern):
                try:
                    sub.queue.put_nowait(event)
                except asyncio.QueueFull:
                    continue

    async def subscribe(self, pattern: str) -> AsyncIterator[CloudEvent]:
        q: asyncio.Queue[CloudEvent] = asyncio.Queue(maxsize=1000)
        sub = Subscription(pattern=pattern, queue=q)
        async with self._lock:
            self._subs.append(sub)
        try:
            while True:
                yield await q.get()
        finally:
            async with self._lock:
                self._subs = [s for s in self._subs if s is not sub]


class RedisDanceFloorEventBus:
    def __init__(self, redis: Redis, channel: str = "dance_floor") -> None:
        self.redis = redis
        self.channel = channel

    async def publish(self, event: CloudEvent) -> None:
        if hasattr(event, "model_dump_json"):
            payload = event.model_dump_json()
        else:
            payload = json.dumps(event.model_dump())
        await self.redis.publish(self.channel, payload)

    async def subscribe(self, pattern: str) -> AsyncIterator[CloudEvent]:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel)
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                data = message.get("data")
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                payload = json.loads(data)
                if hasattr(CloudEvent, "model_validate"):
                    parsed = CloudEvent.model_validate(payload)
                else:
                    parsed = CloudEvent(**payload)
                if fnmatch.fnmatch(parsed.type, pattern):
                    yield parsed
        finally:
            await pubsub.unsubscribe(self.channel)
            await pubsub.close()
