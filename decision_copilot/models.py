# coding: utf-8
import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class DecisionStatus(str, enum.Enum):
    NEW = "new"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class RunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELED = "canceled"


class AgentStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[DecisionStatus] = mapped_column(
        SAEnum(DecisionStatus, name="decision_status"),
        nullable=False,
        default=DecisionStatus.NEW,
        server_default=DecisionStatus.NEW.value,
        index=True,
    )

    final_report: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    runs: Mapped[list["DecisionRun"]] = relationship(
        back_populates="decision",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="decision",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DecisionRun(Base):
    __tablename__ = "decision_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    decision_id: Mapped[int] = mapped_column(
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="default",
        server_default="default",
    )

    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status"),
        nullable=False,
        default=RunStatus.QUEUED,
        server_default=RunStatus.QUEUED.value,
        index=True,
    )

    # Optional but useful: store the orchestrator plan or at least required agents.
    required_agents: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    decision: Mapped["Decision"] = relationship(back_populates="runs")

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="decision_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    decision_id: Mapped[int] = mapped_column(
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    decision_run_id: Mapped[int] = mapped_column(
        ForeignKey("decision_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[AgentStatus] = mapped_column(
        SAEnum(AgentStatus, name="agent_status"),
        nullable=False,
        default=AgentStatus.QUEUED,
        server_default=AgentStatus.QUEUED.value,
        index=True,
    )

    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    output: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    decision: Mapped["Decision"] = relationship(back_populates="agent_runs")
    decision_run: Mapped["DecisionRun"] = relationship(back_populates="agent_runs")


# Practical indexes for common access patterns.
Index("ix_agent_runs_run_agent", AgentRun.decision_run_id, AgentRun.agent_name)
Index("ix_agent_runs_run_status", AgentRun.decision_run_id, AgentRun.status)
