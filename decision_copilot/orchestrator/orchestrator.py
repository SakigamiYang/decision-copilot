# coding: utf-8
from sqlalchemy import select
from sqlalchemy.orm import Session

from decision_copilot.models import (
    AgentRun,
    AgentStatus,
    Decision,
    DecisionRun,
    DecisionStatus,
    RunStatus,
)
from decision_copilot.queue.connection import get_queue


class Orchestrator:
    """
    DB-driven orchestration:
    - Planner runs first and produces required_agents.
    - Required agents run in parallel.
    - Synth runs last after all required agents are DONE.
    - Fail-fast: any required agent FAILED -> run FAILED -> decision FAILED.
    """

    ALLOWED_REQUIRED_AGENTS = ("facts", "pro", "con", "risk")

    def __init__(self, session: Session):
        self.session = session

    def start(self, decision_run_id: int) -> None:
        run = self.session.get(DecisionRun, decision_run_id)
        if run is None:
            raise ValueError(f"DecisionRun not found: {decision_run_id}")

        decision = self.session.get(Decision, run.decision_id)
        if decision is None:
            raise ValueError(f"Decision not found for run: {decision_run_id}")

        # Mark run/decision active early (observable immediately)
        run.status = RunStatus.RUNNING
        decision.status = DecisionStatus.RUNNING
        self.session.commit()

        self._enqueue_if_needed(decision_run_id, "planner")

    def on_agent_done(self, decision_run_id: int, agent_name: str) -> None:
        """
        Called by the worker after it marks AgentRun DONE.
        """
        run = self.session.get(DecisionRun, decision_run_id)
        if run is None:
            return

        if agent_name == "planner":
            self._fanout_required_agents(run)
            return

        # If any required agent failed, fail-fast.
        if self._any_required_failed(run):
            self._fail_run(run, reason="One or more required agents failed.")
            return

        # Only schedule synth after all required agents are done.
        if self._all_required_done(run):
            self._enqueue_if_needed(decision_run_id, "synth")

    def on_agent_failed(self, decision_run_id: int, agent_name: str) -> None:
        """
        Optional hook: call this from the worker when an agent fails.
        For MVP, we fail-fast if it's a required agent.
        """
        run = self.session.get(DecisionRun, decision_run_id)
        if run is None:
            return

        if agent_name in (run.required_agents or []):
            self._fail_run(run, reason=f"Required agent failed: {agent_name}")

    def on_synth_done(self, decision_run_id: int) -> None:
        run = self.session.get(DecisionRun, decision_run_id)
        if run is None:
            return

        decision = self.session.get(Decision, run.decision_id)
        if decision is None:
            return

        synth = self._get_agent_run(decision_run_id, "synth")
        if synth and synth.status == AgentStatus.DONE:
            decision.final_report = synth.output
            decision.status = DecisionStatus.DONE
            run.status = RunStatus.DONE
            self.session.commit()

    def _fanout_required_agents(self, run: DecisionRun) -> None:
        planner = self._get_agent_run(run.id, "planner")

        required = self._normalize_required_agents(planner.output if planner else None)
        run.required_agents = required
        self.session.commit()

        from decision_copilot.queue.tasks import run_agent  # lazy import to avoid circular import

        q = get_queue()
        for name in required:
            self._ensure_agent_run(run.id, name)
            q.enqueue(run_agent, run.id, name)

    def _normalize_required_agents(self, planner_output) -> list[str]:
        # planner_output should be dict with key "required_agents"
        required = []
        if isinstance(planner_output, dict):
            required = planner_output.get("required_agents") or []

        if not isinstance(required, list):
            required = []

        allowed = set(self.ALLOWED_REQUIRED_AGENTS)
        normalized = []
        seen = set()
        for a in required:
            if not isinstance(a, str):
                continue
            a = a.strip()
            if a in allowed and a not in seen:
                normalized.append(a)
                seen.add(a)

        if not normalized:
            normalized = list(self.ALLOWED_REQUIRED_AGENTS)

        return normalized

    def _all_required_done(self, run: DecisionRun) -> bool:
        required = run.required_agents or []
        if not required:
            return False

        stmt = select(AgentRun.agent_name, AgentRun.status).where(
            AgentRun.decision_run_id == run.id,
            AgentRun.agent_name.in_(required),
        )
        rows = list(self.session.execute(stmt).all())
        status_by_name = {name: status for name, status in rows}

        return all(status_by_name.get(name) == AgentStatus.DONE for name in required)

    def _any_required_failed(self, run: DecisionRun) -> bool:
        required = run.required_agents or []
        if not required:
            return False

        stmt = select(AgentRun).where(
            AgentRun.decision_run_id == run.id,
            AgentRun.agent_name.in_(required),
            AgentRun.status == AgentStatus.FAILED,
        )
        return self.session.execute(stmt).scalars().first() is not None

    def _enqueue_if_needed(self, decision_run_id: int, agent_name: str) -> None:
        """
        Enqueue only if:
        - AgentRun exists (create if missing)
        - status is QUEUED (not RUNNING/DONE/FAILED)
        """
        agent_run = self._ensure_agent_run(decision_run_id, agent_name)
        if agent_run.status != AgentStatus.QUEUED:
            return

        from decision_copilot.queue.tasks import run_agent  # lazy import to avoid circular import

        get_queue().enqueue(run_agent, decision_run_id, agent_name)

    def _ensure_agent_run(self, decision_run_id: int, agent_name: str) -> AgentRun:
        existing = self._get_agent_run(decision_run_id, agent_name)
        if existing:
            return existing

        run = self.session.get(DecisionRun, decision_run_id)
        if run is None:
            raise ValueError(f"DecisionRun not found: {decision_run_id}")

        agent_run = AgentRun(
            decision_id=run.decision_id,
            decision_run_id=run.id,
            agent_name=agent_name,
            status=AgentStatus.QUEUED,
        )
        self.session.add(agent_run)
        self.session.commit()
        return agent_run

    def _get_agent_run(self, decision_run_id: int, agent_name: str):
        stmt = (
            select(AgentRun)
            .where(AgentRun.decision_run_id == decision_run_id, AgentRun.agent_name == agent_name)
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def _fail_run(self, run: DecisionRun, reason: str) -> None:
        decision = self.session.get(Decision, run.decision_id)
        if decision:
            decision.status = DecisionStatus.FAILED
            decision.error_message = reason

        run.status = RunStatus.FAILED
        run.error_message = reason
        self.session.commit()
