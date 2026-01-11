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
    p = subparsers.add_parser("run", help="Start a decision run")
    p.add_argument("decision_id", type=int)
    p.add_argument("--mode", type=str, default="default")
    p.set_defaults(func=cmd_run)


def cmd_run(args: argparse.Namespace) -> None:
    svc = _make_service()
    res = svc.start_run(decision_id=args.decision_id, mode=args.mode)
    print(res.decision_run_id)
