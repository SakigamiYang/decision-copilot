# coding: utf-8
import argparse

from decision_copilot.config import AppConfig
from decision_copilot.database import DatabaseConfig, make_engine, init_db


def register(subparsers):
    p = subparsers.add_parser("init-db", help="Initialize SQLite database")
    p.set_defaults(func=cmd_init_db)


def cmd_init_db(args: argparse.Namespace) -> None:
    cfg = AppConfig()
    engine = make_engine(DatabaseConfig(sqlite_path=cfg.sqlite_path))
    init_db(engine)
    print(f"Initialized SQLite database at: {cfg.sqlite_path}")
