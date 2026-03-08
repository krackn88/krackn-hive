from __future__ import annotations

import hashlib
import uuid

from .event_bus import EventBus
from .models import AgentRole, SignalKind, TaskState, utc_now
from .policies import PolicyEngine
from .scoring import RewardEngine
from .schemas import ArtifactSubmit, CloudEvent, SignalCreate
from .scoring import RewardEngine
from .schemas import CloudEvent, SignalCreate
from .scheduler import NectarEconomyScheduler
from .storage import CombRepository


class HiveSwarmService:
    def __init__(
        self,
        repository: CombRepository,
        event_bus: EventBus,
        scheduler: NectarEconomyScheduler,
        reward: RewardEngine,
        policy: PolicyEngine,
    ):
    def __init__(self, repository: CombRepository, event_bus: EventBus, scheduler: NectarEconomyScheduler, reward: RewardEngine):
        self.repository = repository
        self.event_bus = event_bus
        self.scheduler = scheduler
        self.reward = reward
        self.policy = policy

    async def submit_task(self, goal: str, priority: float, constraints: dict) -> str:
        task_id = uuid.uuid4().hex
        task = await self.repository.create_task(task_id, goal, priority, constraints)
        await self.repository.transition_task(task_id, TaskState.triaged)
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

    async def transition_task(self, task_id: str, target: TaskState) -> TaskState | None:
        task = await self.repository.transition_task(task_id, target)
        if task is None:
            return None
        await self.event_bus.publish(
            CloudEvent(
                id=uuid.uuid4().hex,
                type="hive.task.state_changed",
                source="hive.queen",
                time=utc_now(),
                subject=task_id,
                data={"task_id": task_id, "state": task.status.value},
            )
        )
        return task.status

    async def emit_signal(self, signal: SignalCreate) -> str:
        if not self.reward.within_budget(signal):
            signal = SignalCreate(**{**signal.model_dump(), "kind": SignalKind.warning, "summary": "signal over nectar budget"})
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
        queued = await self.repository.list_tasks_by_state(TaskState.planned)
        if not queued:
            queued = await self.repository.list_tasks_by_state(TaskState.triaged)
        if not queued:
            return None

        scored: list[tuple[float, str]] = []
        for task in queued:
            sig = await self.repository.best_signal_for_task(task.task_id)
            signal_bonus = sig.score * sig.confidence if sig else 0.0
            scored.append((task.priority + signal_bonus, task.task_id))
        scored.sort(reverse=True)
        selected_task_id = scored[0][1]

        budget = self.scheduler.budget_for_role(global_budget=global_budget, role=role.name, queued_tasks=len(queued))
        if budget <= 0:
            return None

        task = await self.repository.assign_task(selected_task_id, role.name)
        if task is None:
            return None
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

    async def submit_artifact(self, task_id: str, artifact: ArtifactSubmit) -> dict[str, str]:
        content_hash = hashlib.sha256(artifact.content.encode("utf-8")).hexdigest()
        combined_text = artifact.content + "\n" + str(artifact.metadata)
        violations = self.policy.check_text(combined_text)

        await self.repository.create_artifact(
            artifact_id=uuid.uuid4().hex,
            task_id=task_id,
            producer_agent_id=artifact.producer_agent_id,
            kind=artifact.kind,
            metadata=artifact.metadata,
            content_sha256=content_hash,
        )

        await self.repository.transition_task(task_id, TaskState.review)
        if violations:
            await self.repository.transition_task(task_id, TaskState.active)
            await self.event_bus.publish(
                CloudEvent(
                    id=uuid.uuid4().hex,
                    type="hive.artifact.rejected",
                    source="hive.guard",
                    time=utc_now(),
                    subject=task_id,
                    data={"task_id": task_id, "violations": [v.code for v in violations]},
                )
            )
            return {"status": "rejected", "reason": ",".join(v.code for v in violations)}

        await self.repository.transition_task(task_id, TaskState.done)
        await self.event_bus.publish(
            CloudEvent(
                id=uuid.uuid4().hex,
                type="hive.artifact.approved",
                source="hive.guard",
                time=utc_now(),
                subject=task_id,
                data={"task_id": task_id, "content_sha256": content_hash},
            )
        )
        return {"status": "approved", "content_sha256": content_hash}
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
