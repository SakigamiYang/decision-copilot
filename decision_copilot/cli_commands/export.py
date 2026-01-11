# coding: utf-8
import argparse
from typing import Any

from decision_copilot.config import AppConfig
from decision_copilot.database import DatabaseConfig, make_engine, make_session_factory
from decision_copilot.models import Decision, DecisionRun, AgentRun


def _make_session():
    cfg = AppConfig()
    engine = make_engine(DatabaseConfig(sqlite_path=cfg.sqlite_path))
    SessionFactory = make_session_factory(engine)
    return SessionFactory()


def register(subparsers):
    p = subparsers.add_parser("export", help="Export decision report")
    p.add_argument("decision_id", type=int)
    p.add_argument("--format", choices=["markdown"], default="markdown")
    p.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write output to file instead of stdout",
    )
    p.set_defaults(func=cmd_export)


def cmd_export(args: argparse.Namespace) -> None:
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
    if not run:
        print("No run found for decision")
        return

    agent_runs = (
        session.query(AgentRun)
        .filter(AgentRun.decision_run_id == run.id)
        .all()
    )

    agents: dict[str, dict[str, Any]] = {
        a.agent_name: (a.output or {}) for a in agent_runs
    }

    markdown = _render_markdown(decision, agents)

    if args.output:
        _write_file(args.output, markdown)
        print(f"Report written to: {args.output}")
    else:
        print(markdown)


# =========================
# Rendering
# =========================

def _render_markdown(decision: Decision, agents: dict[str, dict[str, Any]]) -> str:
    md: list[str] = []

    md.append("# Decision Report\n")

    md.append("## Question\n")
    md.append(f"{decision.question}\n")

    if decision.context:
        md.append("## Context\n")
        md.append(f"{decision.context}\n")

    md.append("## Analysis\n")
    _render_list_section(md, "Facts", agents.get("facts"))
    _render_list_section(md, "Pros", agents.get("pro"))
    _render_list_section(md, "Cons", agents.get("con"))
    _render_list_section(md, "Risks", agents.get("risk"))

    if decision.final_report:
        md.append("## Final Recommendation\n")
        _render_final_report(md, decision.final_report)

    return "\n".join(md)


# =========================
# Helpers
# =========================

def _render_list_section(md: list[str], title: str, data: dict | None) -> None:
    if not data:
        return

    items = []
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        items = data["items"]

    md.append(f"### {title}\n")

    if not items:
        md.append("_No items provided._\n")
        return

    for it in items:
        md.append(f"- {it}")
    md.append("")


def _render_final_report(md: list[str], report: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        md.append("_Invalid final report format._\n")
        return

    if report.get("recommendation"):
        md.append(f"**Recommendation**: {report['recommendation']}\n")

    if report.get("confidence") is not None:
        md.append(f"**Confidence**: {report['confidence']}\n")

    if report.get("rationale"):
        md.append("**Rationale**:\n")
        md.append(f"{report['rationale']}\n")

    _render_bullets(md, "Key Trade-offs", report.get("key_tradeoffs"))
    _render_bullets(md, "Next Steps", report.get("next_steps"))
    _render_bullets(md, "Open Questions", report.get("open_questions"))


def _render_bullets(md: list[str], title: str, value: Any) -> None:
    if not value:
        return

    md.append(f"**{title}**:\n")

    if isinstance(value, list):
        for v in value:
            md.append(f"- {v}")
    else:
        md.append(f"- {value}")

    md.append("")


def _write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
