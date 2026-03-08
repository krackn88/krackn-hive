from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Caste(str, Enum):
    queen = "queen"
    scout = "scout"
    worker = "worker"
    guard = "guard"
    drone = "drone"


class AgentState(str, Enum):
    booting = "booting"
    idle = "idle"
    assigned = "assigned"
    executing = "executing"
    reporting = "reporting"
    blocked = "blocked"
    quarantined = "quarantined"
    retired = "retired"


class TaskState(str, Enum):
    discovered = "discovered"
    triaged = "triaged"
    planned = "planned"
    assigned = "assigned"
    active = "active"
    review = "review"
    done = "done"
    blocked = "blocked"
    rejected = "rejected"
    archived = "archived"


class SignalKind(str, Enum):
    opportunity = "opportunity"
    warning = "warning"
    completion = "completion"
    failure = "failure"
    resource = "resource"


try:
    from sqlalchemy import JSON, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class HiveTask(Base):
        __tablename__ = "hive_tasks"

        task_id: Mapped[str] = mapped_column(String(32), primary_key=True)
        goal: Mapped[str] = mapped_column(Text, nullable=False)
        status: Mapped[TaskState] = mapped_column(SqlEnum(TaskState), default=TaskState.discovered, nullable=False)
        priority: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
        constraints_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
        deps_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
        assigned_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    class HiveSignal(Base):
        __tablename__ = "hive_signals"

        signal_id: Mapped[str] = mapped_column(String(32), primary_key=True)
        task_id: Mapped[str] = mapped_column(ForeignKey("hive_tasks.task_id", ondelete="CASCADE"), nullable=False)
        kind: Mapped[SignalKind] = mapped_column(SqlEnum(SignalKind), nullable=False)
        source_agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
        score: Mapped[float] = mapped_column(Float, nullable=False)
        confidence: Mapped[float] = mapped_column(Float, nullable=False)
        estimated_cost_json: Mapped[dict[str, int]] = mapped_column(JSON, default=dict, nullable=False)
        payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
        summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    class HiveAgent(Base):
        __tablename__ = "hive_agents"

        agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
        caste: Mapped[Caste] = mapped_column(SqlEnum(Caste), nullable=False)
        state: Mapped[AgentState] = mapped_column(SqlEnum(AgentState), default=AgentState.booting, nullable=False)
        capabilities_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
        trust_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
        cost_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
        sandbox_profile: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
        last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    class HiveArtifact(Base):
        __tablename__ = "hive_artifacts"

        artifact_id: Mapped[str] = mapped_column(String(32), primary_key=True)
        task_id: Mapped[str] = mapped_column(ForeignKey("hive_tasks.task_id", ondelete="CASCADE"), nullable=False)
        producer_agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
        kind: Mapped[str] = mapped_column(String(32), nullable=False)
        uri: Mapped[str | None] = mapped_column(Text, nullable=True)
        content_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
        metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    class AgentRole(Base):
        __tablename__ = "agent_roles"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
        capabilities_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
        concurrency_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
except ModuleNotFoundError:
    class Base:  # pragma: no cover
        metadata = None

    class HiveTask:  # pragma: no cover
        pass

    class HiveSignal:  # pragma: no cover
        pass

    class HiveAgent:  # pragma: no cover
        pass

    class HiveArtifact:  # pragma: no cover
        pass

    class AgentRole:  # pragma: no cover
        pass
