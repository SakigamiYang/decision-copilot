# coding: utf-8
import argparse

from decision_copilot.config import AppConfig
from decision_copilot.database import DatabaseConfig, make_engine, make_session_factory
from decision_copilot.models import Decision


def _make_session():
    cfg = AppConfig()
    engine = make_engine(DatabaseConfig(sqlite_path=cfg.sqlite_path))
    SessionFactory = make_session_factory(engine)
    return SessionFactory()


def register(subparsers):
    p = subparsers.add_parser("list", help="List decisions")
    p.add_argument("--status", type=str, default=None)
    p.set_defaults(func=cmd_list)


def cmd_list(args: argparse.Namespace) -> None:
    session = _make_session()
    q = session.query(Decision)
    if args.status:
        q = q.filter(Decision.status == args.status)

    rows = q.order_by(Decision.created_at.desc()).limit(20).all()

    for d in rows:
        print(f"{d.id}\t{d.status}\t{d.question}")
