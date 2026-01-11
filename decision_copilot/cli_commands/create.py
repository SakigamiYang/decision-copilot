# coding: utf-8
import argparse

from decision_copilot.config import AppConfig
from decision_copilot.database import DatabaseConfig, make_engine, make_session_factory
from decision_copilot.services.decision_service import DecisionService


def _make_service() -> DecisionService:
    cfg = AppConfig()
    engine = make_engine(DatabaseConfig(sqlite_path=cfg.sqlite_path))
    SessionFactory = make_session_factory(engine)
    return DecisionService(SessionFactory())


def register(subparsers):
    p = subparsers.add_parser("create", help="Create a decision")
    p.add_argument("question", type=str)
    p.add_argument("--context", type=str, default=None)
    p.set_defaults(func=cmd_create)


def cmd_create(args: argparse.Namespace) -> None:
    svc = _make_service()
    res = svc.create_decision(question=args.question, context=args.context)
    print(res.decision_id)
