# coding: utf-8
import argparse

from dotenv import load_dotenv

from decision_copilot.cli_commands import (
    init_db,
    create,
    run,
    status,
    report,
    list_cmd,
    explain,
    export,
)

load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="decision-copilot")
    sub = p.add_subparsers(dest="cmd", required=True)

    init_db.register(sub)
    create.register(sub)
    run.register(sub)
    status.register(sub)
    report.register(sub)
    list_cmd.register(sub)
    explain.register(sub)
    export.register(sub)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
