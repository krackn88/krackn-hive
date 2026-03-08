from __future__ import annotations

import importlib.util
from datetime import datetime
from enum import Enum
from typing import Any

_HAS_PYDANTIC = importlib.util.find_spec("pydantic") is not None

if _HAS_PYDANTIC:
    from pydantic import BaseModel, ConfigDict, Field
else:
    class BaseModel:  # type: ignore[override]
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self, mode: str | None = None):
            return self.__dict__.copy()

    def Field(default=None, default_factory=None, ge=None, le=None):  # type: ignore
        if default_factory is not None:
            return default_factory()
        return default

    def ConfigDict(**kwargs):  # type: ignore
        return kwargs
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import AgentState, Caste, SignalKind, TaskState


class EventType(str, Enum):
    task_created = "hive.task.created"
    task_state_changed = "hive.task.state_changed"
    task_assigned = "hive.task.assigned"
    signal_emitted = "hive.signal.emitted"
    artifact_approved = "hive.artifact.approved"
    artifact_rejected = "hive.artifact.rejected"


class EstimatedCost(BaseModel):
    tokens: int = 0
    wall_seconds: int = 0
    sandbox_seconds: int = 0


class CloudEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specversion: str = "1.0"
    id: str
    type: str
    source: str
    time: datetime
    datacontenttype: str = "application/json"
    subject: str | None = None
    traceparent: str | None = None
    tracestate: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class TaskCreate(BaseModel):
    goal: str
    priority: float = 1.0
    constraints: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class TaskTransition(BaseModel):
    state: TaskState


class TaskRead(BaseModel):
    task_id: str
    goal: str
    status: TaskState
    priority: float
    constraints: dict[str, Any]
    dependencies: list[str]
    assigned_agents: list[str]
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None


class SignalCreate(BaseModel):
    task_id: str
    kind: SignalKind
    source_agent_id: str
    score: float = Field(ge=0, le=1, default=0.5)
    confidence: float = Field(ge=0, le=1, default=0.5)
    estimated_cost: EstimatedCost = Field(default_factory=EstimatedCost)
    payload: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    idempotency_key: str | None = None


class ArtifactSubmit(BaseModel):
    producer_agent_id: str
    kind: str = "patch"
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    estimated_cost: EstimatedCost = Field(default_factory=EstimatedCost)
    payload: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""


class RoleCreate(BaseModel):
    name: str
    capabilities: list[str]
    concurrency_limit: int = Field(default=1, ge=1)


class RoleRead(BaseModel):
    id: int
    name: str
    capabilities: list[str]
    concurrency_limit: int


class AgentRegister(BaseModel):
    agent_id: str
    caste: Caste
    capabilities: list[str] = Field(default_factory=list)
    sandbox_profile: str = "none"


class AgentRead(BaseModel):
    agent_id: str
    caste: Caste
    state: AgentState
    capabilities: list[str]


class HiveSummary(BaseModel):
    discovered: int = 0
    triaged: int = 0
    planned: int = 0
    assigned: int = 0
    active: int = 0
    review: int = 0
    done: int = 0
    blocked: int = 0
    rejected: int = 0
    archived: int = 0
