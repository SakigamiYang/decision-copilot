# coding: utf-8
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from decision_copilot.models import (
    AgentRun,
    Decision,
    DecisionRun,
    DecisionStatus,
    RunStatus,
)
from decision_copilot.orchestrator.orchestrator import Orchestrator


@dataclass(frozen=True)
class CreateDecisionResult:
    decision_id: int


@dataclass(frozen=True)
class StartRunResult:
    decision_run_id: int


class DecisionService:
    """Application service for decision lifecycle operations."""

    def __init__(self, session: Session):
        self.session = session

    def init_db(self) -> None:
        # Intentionally empty here; init_db is handled in database.py.
        # This method exists only to keep the CLI service-oriented.
        return

    def create_decision(self, question: str, context: Optional[str] = None) -> CreateDecisionResult:
        decision = Decision(
            question=question,
            context=context,
            status=DecisionStatus.NEW,
        )
        self.session.add(decision)
        self.session.commit()
        return CreateDecisionResult(decision_id=decision.id)

    def start_run(self, decision_id: int, mode: str = "default") -> StartRunResult:
        decision = self._get_decision(decision_id)

        run = DecisionRun(
            decision_id=decision.id,
            mode=mode,
            status=RunStatus.QUEUED,
        )
        self.session.add(run)
        decision.status = DecisionStatus.RUNNING
        self.session.commit()

        Orchestrator(self.session).start(run.id)
        return StartRunResult(decision_run_id=run.id)

    def get_decision(self, decision_id: int) -> Decision:
        return self._get_decision(decision_id)

    def get_latest_run(self, decision_id: int) -> Optional[DecisionRun]:
        stmt = (
            select(DecisionRun)
            .where(DecisionRun.decision_id == decision_id)
            .order_by(desc(DecisionRun.created_at), desc(DecisionRun.id))
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def get_agent_runs(self, decision_run_id: int) -> list[AgentRun]:
        stmt = (
            select(AgentRun)
            .where(AgentRun.decision_run_id == decision_run_id)
            .order_by(AgentRun.created_at.asc(), AgentRun.id.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_status_snapshot(self, decision_id: int) -> dict:
        decision = self._get_decision(decision_id)
        run = self.get_latest_run(decision_id)

        snapshot = {
            "decision": {
                "id": decision.id,
                "status": decision.status.value,
                "question": decision.question,
                "created_at": decision.created_at.isoformat(),
                "updated_at": decision.updated_at.isoformat(),
            },
            "latest_run": None,
            "agent_runs": [],
        }

        if run is None:
            return snapshot

        agent_runs = self.get_agent_runs(run.id)

        snapshot["latest_run"] = {
            "id": run.id,
            "mode": run.mode,
            "status": run.status.value,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
        }

        snapshot["agent_runs"] = [
            {
                "id": ar.id,
                "agent_name": ar.agent_name,
                "status": ar.status.value,
                "latency_ms": ar.latency_ms,
                "model": ar.model,
                "error_message": ar.error_message,
                "created_at": ar.created_at.isoformat(),
                "updated_at": ar.updated_at.isoformat(),
            }
            for ar in agent_runs
        ]

        return snapshot

    def get_report(self, decision_id: int) -> dict:
        decision = self._get_decision(decision_id)
        return {
            "decision_id": decision.id,
            "status": decision.status.value,
            "final_report": decision.final_report,
            "error_message": decision.error_message,
        }

    def _get_decision(self, decision_id: int) -> Decision:
        decision = self.session.get(Decision, decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id}")
        return decision
