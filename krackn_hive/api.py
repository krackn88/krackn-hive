from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .abandonment import TaskAbandonmentService
from .config import settings
from .db import get_session
from .event_bus import InMemoryEventBus
from .registry import AgentRoleRegistry
from .schemas import AgentRead, AgentRegister, RoleCreate, RoleRead, SignalCreate, TaskCreate, TaskRead
from .scheduler import NectarEconomyScheduler
from .scoring import NectarBudget, RewardEngine
from .storage import CombRepository
from .swarm import HiveSwarmService

router = APIRouter()
_event_bus = InMemoryEventBus()


async def deps(session: AsyncSession = Depends(get_session)) -> tuple[HiveSwarmService, CombRepository, AgentRoleRegistry, TaskAbandonmentService]:
    repo = CombRepository(session)
    swarm = HiveSwarmService(
        repository=repo,
        event_bus=_event_bus,
        scheduler=NectarEconomyScheduler(),
        reward=RewardEngine(NectarBudget(max_tokens_per_task=settings.global_budget_tokens * 1000)),
    )
    registry = AgentRoleRegistry(session)
    abandonment = TaskAbandonmentService(repo, _event_bus, settings.abandonment_ttl_seconds)
    return swarm, repo, registry, abandonment


@router.post("/tasks", response_model=TaskRead)
async def create_task(data: TaskCreate, bundle=Depends(deps)) -> TaskRead:
    swarm, repo, _, _ = bundle
    task_id = await swarm.submit_task(goal=data.goal, priority=data.priority, constraints=data.constraints)
    task = await repo.get_task(task_id)
    return TaskRead(
        task_id=task.task_id,
        goal=task.goal,
        status=task.status,
        priority=task.priority,
        constraints=task.constraints_json,
        dependencies=task.deps_json,
        assigned_agents=task.assigned_json,
    )


@router.post("/signals")
async def emit_signal(data: SignalCreate, bundle=Depends(deps)) -> dict[str, str]:
    swarm, repo, _, _ = bundle
    task = await repo.get_task(data.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    signal_id = await swarm.emit_signal(data)
    return {"signal_id": signal_id}


@router.post("/roles", response_model=RoleRead)
async def create_role(data: RoleCreate, bundle=Depends(deps)) -> RoleRead:
    _, _, registry, _ = bundle
    role = await registry.register(data.name, data.capabilities, data.concurrency_limit)
    return RoleRead(id=role.id, name=role.name, capabilities=role.capabilities_json, concurrency_limit=role.concurrency_limit)


@router.post("/dispatch/{role_name}")
async def dispatch(role_name: str, bundle=Depends(deps)) -> dict[str, str]:
    swarm, repo, _, _ = bundle
    role = await repo.get_role(role_name)
    if role is None:
        raise HTTPException(status_code=404, detail="role not found")
    task_id = await swarm.assign_next(role=role, global_budget=settings.global_budget_tokens)
    if task_id is None:
        raise HTTPException(status_code=404, detail="no assignable task")
    return {"task_id": task_id}


@router.post("/agents", response_model=AgentRead)
async def register_agent(data: AgentRegister, bundle=Depends(deps)) -> AgentRead:
    _, repo, _, _ = bundle
    agent = await repo.register_agent(data.agent_id, data.caste, data.capabilities, data.sandbox_profile)
    return AgentRead(agent_id=agent.agent_id, caste=agent.caste, state=agent.state, capabilities=agent.capabilities_json)


@router.post("/abandonment/sweep")
async def sweep(bundle=Depends(deps)) -> dict[str, int]:
    _, _, _, abandonment = bundle
    return {"abandoned": await abandonment.sweep()}
