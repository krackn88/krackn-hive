from __future__ import annotations

import uuid

from .event_bus import EventBus
from .models import AgentRole, SignalKind, TaskState, utc_now
from .scoring import RewardEngine
from .schemas import CloudEvent, SignalCreate
from .scheduler import NectarEconomyScheduler
from .storage import CombRepository


class HiveSwarmService:
    def __init__(self, repository: CombRepository, event_bus: EventBus, scheduler: NectarEconomyScheduler, reward: RewardEngine):
        self.repository = repository
        self.event_bus = event_bus
        self.scheduler = scheduler
        self.reward = reward

    async def submit_task(self, goal: str, priority: float, constraints: dict) -> str:
        task_id = uuid.uuid4().hex
        task = await self.repository.create_task(task_id, goal, priority, constraints)
        await self.event_bus.publish(
            CloudEvent(
                id=uuid.uuid4().hex,
                type="hive.task.created",
                source="hive.queen",
                time=utc_now(),
                subject=task_id,
                data={"task_id": task_id, "goal": task.goal, "priority": task.priority},
            )
        )
        return task_id

    async def emit_signal(self, signal: SignalCreate) -> str:
        signal_id = uuid.uuid4().hex
        await self.repository.create_signal(
            signal_id=signal_id,
            task_id=signal.task_id,
            kind=signal.kind,
            source_agent_id=signal.source_agent_id,
            score=signal.score,
            confidence=signal.confidence,
            estimated_cost_json=signal.estimated_cost.model_dump(),
            payload_json=signal.payload,
            summary=signal.summary,
        )
        await self.event_bus.publish(
            CloudEvent(
                id=uuid.uuid4().hex,
                type="hive.signal.emitted",
                source=signal.source_agent_id,
                time=utc_now(),
                subject=signal.task_id,
                data={"signal_id": signal_id, **signal.model_dump(mode="json")},
            )
        )
        return signal_id

    async def assign_next(self, role: AgentRole, global_budget: int = 50) -> str | None:
        queued = await self.repository.list_tasks_by_state(TaskState.discovered)
        if not queued:
            queued = await self.repository.list_tasks_by_state(TaskState.planned)
        if not queued:
            return None
        budget = self.scheduler.budget_for_role(global_budget=global_budget, role=role.name, queued_tasks=len(queued))
        if budget <= 0:
            return None
        task = queued[0]
        await self.repository.assign_task(task.task_id, role.name)
        await self.event_bus.publish(
            CloudEvent(
                id=uuid.uuid4().hex,
                type="hive.task.assigned",
                source="hive.queen",
                time=utc_now(),
                subject=task.task_id,
                data={"task_id": task.task_id, "role": role.name, "budget": budget},
            )
        )
        return task.task_id

    async def publish_artifact_result(self, task_id: str, agent_id: str, content: str, approved: bool) -> None:
        state = TaskState.done if approved else TaskState.active
        await self.repository.update_task_state(task_id, state)
        event_type = "hive.artifact.approved" if approved else "hive.artifact.rejected"
        await self.event_bus.publish(
            CloudEvent(
                id=uuid.uuid4().hex,
                type=event_type,
                source=agent_id,
                time=utc_now(),
                subject=task_id,
                data={"task_id": task_id, "content": content},
            )
        )
