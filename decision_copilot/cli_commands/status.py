# coding: utf-8
import argparse
import json

from decision_copilot.config import AppConfig
from decision_copilot.database import DatabaseConfig, make_engine, make_session_factory
from decision_copilot.services.decision_service import DecisionService


def _make_service() -> DecisionService:
    cfg = AppConfig()
    engine = make_engine(DatabaseConfig(sqlite_path=cfg.sqlite_path))
    SessionFactory = make_session_factory(engine)
    return DecisionService(SessionFactory())


def register(subparsers):
    p = subparsers.add_parser("status", help="Show decision status snapshot")
    p.add_argument("decision_id", type=int)
    p.set_defaults(func=cmd_status)


def cmd_status(args: argparse.Namespace) -> None:
    svc = _make_service()
    snap = svc.get_status_snapshot(decision_id=args.decision_id)
    print(json.dumps(snap, indent=2, ensure_ascii=False))
