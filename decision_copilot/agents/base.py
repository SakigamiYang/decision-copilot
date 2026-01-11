# coding: utf-8
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class AgentContext:
    decision_id: int
    decision_run_id: int
    question: str
    context: str | None


class Agent(Protocol):
    name: str

    def run(self, ctx: AgentContext, inputs: dict[str, Any]) -> dict[str, Any]:
        ...
