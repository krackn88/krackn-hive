from datetime import timedelta

from .event_bus import EventBus
from .models import TaskState, utc_now
from .schemas import CloudEvent, EventType
from .schemas import CloudEvent
from .storage import CombRepository


class TaskAbandonmentService:
    def __init__(self, repository: CombRepository, event_bus: EventBus, ttl_seconds: int):
        self.repository = repository
        self.event_bus = event_bus
        self.ttl_seconds = ttl_seconds

    async def sweep(self) -> int:
        cutoff = utc_now() - timedelta(seconds=self.ttl_seconds)
        stale = await self.repository.abandon_stale_assignments(cutoff)
        for task in stale:
            await self.event_bus.publish(
                CloudEvent(
                    id=f"abandon-{task.task_id}-{int(utc_now().timestamp())}",
                    type=EventType.task_state_changed.value,
                    type="hive.task.state_changed",
                    source="hive.abandonment",
                    time=utc_now(),
                    subject=task.task_id,
                    data={"task_id": task.task_id, "state": TaskState.blocked.value},
                )
            )
        return len(stale)
