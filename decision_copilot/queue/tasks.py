# coding: utf-8
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from decision_copilot.agents.base import AgentContext
from decision_copilot.agents.cons import ConAgent
from decision_copilot.agents.facts import FactsAgent
from decision_copilot.agents.planner import PlannerAgent
from decision_copilot.agents.pros import ProAgent
from decision_copilot.agents.risks import RiskAgent
from decision_copilot.agents.synth import SynthAgent
from decision_copilot.config import AppConfig
from decision_copilot.database import DatabaseConfig, make_engine, make_session_factory
from decision_copilot.llm.client import DeepSeekClient
from decision_copilot.models import (
    AgentRun,
    AgentStatus,
    Decision,
    DecisionRun,
)
from decision_copilot.orchestrator.orchestrator import Orchestrator


def _make_session_factory_from_config() -> Any:
    cfg = AppConfig()
    engine = make_engine(DatabaseConfig(sqlite_path=cfg.sqlite_path))
    return make_session_factory(engine)


def _make_llm() -> DeepSeekClient:
    # Reads DEEPSEEK_BASE_URL / DEEPSEEK_API_KEY / DEEPSEEK_MODEL from env.
    return DeepSeekClient()


def _build_agent(agent_name: str) -> Any:
    llm = _make_llm()

    if agent_name == "planner":
        return PlannerAgent(llm)
    if agent_name == "facts":
        return FactsAgent(llm)
    if agent_name == "pro":
        return ProAgent(llm)
    if agent_name == "con":
        return ConAgent(llm)
    if agent_name == "risk":
        return RiskAgent(llm)
    if agent_name == "synth":
        return SynthAgent(llm)

    raise ValueError(f"Unknown agent: {agent_name}")


def run_agent(decision_run_id: int, agent_name: str) -> None:
    """
    RQ task: execute one agent for the given decision_run_id, persist status/output,
    then trigger orchestration callbacks.

    This function must be idempotent enough to tolerate retries:
    - If the AgentRun row is missing, it no-ops.
    - It always writes status transitions into SQLite.
    """
    SessionFactory = _make_session_factory_from_config()

    with SessionFactory() as session:
        run = session.get(DecisionRun, decision_run_id)
        if run is None:
            return

        decision = session.get(Decision, run.decision_id)
        if decision is None:
            return

        agent_run = _get_agent_run(session, decision_run_id, agent_name)
        if agent_run is None:
            return

        # If already done, do not rerun implicitly.
        if agent_run.status == AgentStatus.DONE:
            return

        agent_run.status = AgentStatus.RUNNING
        session.commit()

        start = time.time()
        try:
            agent = _build_agent(agent_name)

            ctx = AgentContext(
                decision_id=decision.id,
                decision_run_id=run.id,
                question=decision.question,
                context=decision.context,
            )

            inputs: dict[str, Any] = {}
            if agent_name == "synth":
                inputs = _load_downstream_outputs(session, decision_run_id)

            output = agent.run(ctx, inputs)

            agent_run.output = output
            agent_run.latency_ms = int((time.time() - start) * 1000)
            agent_run.status = AgentStatus.DONE
            session.commit()

            orch = Orchestrator(session)
            orch.on_agent_done(decision_run_id, agent_name)
            if agent_name == "synth":
                orch.on_synth_done(decision_run_id)

        except Exception as e:
            agent_run.status = AgentStatus.FAILED
            agent_run.error_message = str(e)
            agent_run.latency_ms = int((time.time() - start) * 1000)
            session.commit()

            orch = Orchestrator(session)
            orch.on_agent_failed(decision_run_id, agent_name)


def _get_agent_run(session: Session, decision_run_id: int, agent_name: str) -> AgentRun | None:
    stmt = (
        select(AgentRun)
        .where(AgentRun.decision_run_id == decision_run_id, AgentRun.agent_name == agent_name)
        .limit(1)
    )
    return session.execute(stmt).scalars().first()


def _load_downstream_outputs(session: Session, decision_run_id: int) -> dict[str, Any]:
    """
    Load DONE outputs from facts/pro/con/risk for synth.
    Returns a dict keyed by agent name.
    """
    stmt = (
        select(AgentRun)
        .where(
            AgentRun.decision_run_id == decision_run_id,
            AgentRun.status == AgentStatus.DONE,
            AgentRun.agent_name.in_(["facts", "pro", "con", "risk"]),
        )
    )
    rows = list(session.execute(stmt).scalars().all())

    out: dict[str, Any] = {}
    for r in rows:
        out[r.agent_name] = r.output or {}
    return out
