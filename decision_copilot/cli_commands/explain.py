# coding: utf-8
import argparse
import json

from decision_copilot.config import AppConfig
from decision_copilot.database import DatabaseConfig, make_engine, make_session_factory
from decision_copilot.models import Decision, DecisionRun, AgentRun


def _make_session():
    cfg = AppConfig()
    engine = make_engine(DatabaseConfig(sqlite_path=cfg.sqlite_path))
    SessionFactory = make_session_factory(engine)
    return SessionFactory()


def register(subparsers):
    p = subparsers.add_parser("explain", help="Explain decision execution")
    p.add_argument("decision_id", type=int)
    p.set_defaults(func=cmd_explain)


def cmd_explain(args: argparse.Namespace) -> None:
    session = _make_session()

    decision = session.get(Decision, args.decision_id)
    if not decision:
        print("Decision not found")
        return

    run = (
        session.query(DecisionRun)
        .filter(DecisionRun.decision_id == decision.id)
        .order_by(DecisionRun.created_at.desc())
        .first()
    )

    agents = (
        session.query(AgentRun)
        .filter(AgentRun.decision_run_id == run.id)
        .order_by(AgentRun.created_at)
        .all()
    )

    print(f"Decision {decision.id}")
    print(f"Question: {decision.question}")
    print(f"Status: {decision.status}")
    print()

    for a in agents:
        print(f"[{a.agent_name}] {a.status}")
        if a.output:
            print(json.dumps(a.output, indent=2, ensure_ascii=False))
        if a.error_message:
            print(f"ERROR: {a.error_message}")
        print()
