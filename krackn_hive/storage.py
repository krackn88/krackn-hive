from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .lifecycle import can_transition
from .models import AgentState, AgentRole, Caste, HiveAgent, HiveArtifact, HiveSignal, HiveTask, SignalKind, TaskState, lease_until, utc_now
from .models import AgentState, AgentRole, Caste, HiveAgent, HiveArtifact, HiveSignal, HiveTask, SignalKind, TaskState, utc_now


class InvalidTransitionError(ValueError):
    pass


class CombRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        task_id: str,
        goal: str,
        priority: float,
        constraints: dict,
        idempotency_key: str | None = None,
    ) -> HiveTask:
        if idempotency_key:
            existing = await self.get_task_by_idempotency(idempotency_key)
            if existing:
                return existing

        task = HiveTask(
            task_id=task_id,
            idempotency_key=idempotency_key,
    async def create_task(self, task_id: str, goal: str, priority: float, constraints: dict) -> HiveTask:
        task = HiveTask(
            task_id=task_id,
            goal=goal,
            priority=priority,
            status=TaskState.discovered,
            constraints_json=constraints,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task_by_idempotency(self, idempotency_key: str) -> HiveTask | None:
        result = await self.session.execute(select(HiveTask).where(HiveTask.idempotency_key == idempotency_key))
        return result.scalar_one_or_none()

    async def get_task(self, task_id: str) -> HiveTask | None:
        return await self.session.get(HiveTask, task_id)

    async def list_tasks_by_state(self, state: TaskState, limit: int = 50) -> list[HiveTask]:
        result = await self.session.execute(
            select(HiveTask).where(HiveTask.status == state).order_by(HiveTask.priority.desc(), HiveTask.updated_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def task_summary(self) -> dict[str, int]:
        summary: dict[str, int] = {state.value: 0 for state in TaskState}
        result = await self.session.execute(select(HiveTask.status, func.count(HiveTask.task_id)).group_by(HiveTask.status))
        for status, count in result.all():
            summary[status.value] = int(count)
        return summary

    async def transition_task(self, task_id: str, target_state: TaskState) -> HiveTask | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if task.status != target_state and not can_transition(task.status, target_state):
            raise InvalidTransitionError(f"invalid transition {task.status.value} -> {target_state.value}")
        task.status = target_state
        task.updated_at = utc_now()
        if target_state in {TaskState.done, TaskState.archived, TaskState.rejected}:
            task.lease_owner = None
            task.lease_expires_at = None
    async def update_task_state(self, task_id: str, state: TaskState) -> HiveTask | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        task.status = state
        task.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def assign_task(self, task_id: str, agent_id: str, lease_seconds: int = 300) -> HiveTask | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if task.status in {TaskState.discovered, TaskState.triaged}:
            task.status = TaskState.planned
        await self.transition_task(task_id, TaskState.assigned)
        task = await self.get_task(task_id)
    async def assign_task(self, task_id: str, agent_id: str) -> HiveTask | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        assigned = list(task.assigned_json)
        if agent_id not in assigned:
            assigned.append(agent_id)
        task.assigned_json = assigned
        task.lease_owner = agent_id
        task.lease_expires_at = lease_until(lease_seconds)
        task.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def renew_lease(self, task_id: str, agent_id: str, lease_seconds: int = 300) -> HiveTask | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if task.lease_owner != agent_id:
            return None
        task.lease_expires_at = lease_until(lease_seconds)
        task.status = TaskState.assigned
        task.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def create_signal(
        self,
        signal_id: str,
        task_id: str,
        kind: SignalKind,
        kind,
        source_agent_id: str,
        score: float,
        confidence: float,
        estimated_cost_json: dict,
        payload_json: dict,
        summary: str,
        idempotency_key: str | None = None,
    ) -> HiveSignal:
        if idempotency_key:
            result = await self.session.execute(select(HiveSignal).where(HiveSignal.idempotency_key == idempotency_key))
            existing = result.scalar_one_or_none()
            if existing:
                return existing

        signal = HiveSignal(
            signal_id=signal_id,
            idempotency_key=idempotency_key,
    ) -> HiveSignal:
        signal = HiveSignal(
            signal_id=signal_id,
            task_id=task_id,
            kind=kind,
            source_agent_id=source_agent_id,
            score=score,
            confidence=confidence,
            estimated_cost_json=estimated_cost_json,
            payload_json=payload_json,
            summary=summary,
            created_at=utc_now(),
        )
        self.session.add(signal)
        await self.session.commit()
        await self.session.refresh(signal)
        return signal

    async def best_signal_for_task(self, task_id: str) -> HiveSignal | None:
        result = await self.session.execute(
            select(HiveSignal)
            .where(HiveSignal.task_id == task_id)
            .order_by((HiveSignal.score * HiveSignal.confidence).desc(), HiveSignal.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def register_agent(self, agent_id: str, caste: Caste, capabilities: list[str], sandbox_profile: str) -> HiveAgent:
        existing = await self.session.get(HiveAgent, agent_id)
        if existing:
            existing.caste = caste
            existing.capabilities_json = capabilities
            existing.sandbox_profile = sandbox_profile
            existing.state = AgentState.idle
            existing.last_heartbeat_at = utc_now()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

    async def register_agent(self, agent_id: str, caste: Caste, capabilities: list[str], sandbox_profile: str) -> HiveAgent:
        agent = HiveAgent(
            agent_id=agent_id,
            caste=caste,
            state=AgentState.idle,
            capabilities_json=capabilities,
            sandbox_profile=sandbox_profile,
            last_heartbeat_at=utc_now(),
        )
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def heartbeat(self, agent_id: str) -> HiveAgent | None:
        agent = await self.session.get(HiveAgent, agent_id)
        if not agent:
            return None
        agent.last_heartbeat_at = utc_now()
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def upsert_role(self, name: str, capabilities: list[str], concurrency_limit: int) -> AgentRole:
        result = await self.session.execute(select(AgentRole).where(AgentRole.name == name))
        role = result.scalar_one_or_none()
        if role is None:
            role = AgentRole(name=name, capabilities_json=capabilities, concurrency_limit=concurrency_limit)
            self.session.add(role)
        else:
            role.capabilities_json = capabilities
            role.concurrency_limit = concurrency_limit
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def get_role(self, name: str) -> AgentRole | None:
        result = await self.session.execute(select(AgentRole).where(AgentRole.name == name))
        return result.scalar_one_or_none()

    async def create_artifact(
        self,
        artifact_id: str,
        task_id: str,
        producer_agent_id: str,
        kind: str,
        metadata: dict,
        content_sha256: str | None = None,
        idempotency_key: str | None = None,
    ) -> HiveArtifact:
        if idempotency_key:
            result = await self.session.execute(select(HiveArtifact).where(HiveArtifact.idempotency_key == idempotency_key))
            existing = result.scalar_one_or_none()
            if existing:
                return existing

        artifact = HiveArtifact(
            artifact_id=artifact_id,
            idempotency_key=idempotency_key,
    async def create_artifact(self, artifact_id: str, task_id: str, producer_agent_id: str, kind: str, metadata: dict) -> HiveArtifact:
        artifact = HiveArtifact(
            artifact_id=artifact_id,
            task_id=task_id,
            producer_agent_id=producer_agent_id,
            kind=kind,
            metadata_json=metadata,
            content_sha256=content_sha256,
            created_at=utc_now(),
        )
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        return artifact

    async def abandon_stale_assignments(self, cutoff: datetime) -> list[HiveTask]:
        result = await self.session.execute(
            select(HiveTask).where(
                HiveTask.status.in_([TaskState.assigned, TaskState.active]),
                HiveTask.lease_expires_at.is_not(None),
                HiveTask.lease_expires_at < cutoff,
            )
            select(HiveTask).where(HiveTask.status.in_([TaskState.assigned, TaskState.active]), HiveTask.updated_at < cutoff)
        )
        stale = list(result.scalars().all())
        for task in stale:
            task.status = TaskState.blocked
            task.lease_owner = None
            task.lease_expires_at = None
            task.updated_at = utc_now()
        if stale:
            await self.session.commit()
            for task in stale:
                await self.session.refresh(task)
        return stale
