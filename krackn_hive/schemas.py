from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import AgentState, Caste, SignalKind, TaskState


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


class TaskRead(BaseModel):
    task_id: str
    goal: str
    status: TaskState
    priority: float
    constraints: dict[str, Any]
    dependencies: list[str]
    assigned_agents: list[str]


class SignalCreate(BaseModel):
    task_id: str
    kind: SignalKind
    source_agent_id: str
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
