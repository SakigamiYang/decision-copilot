# coding: utf-8
from decision_copilot.agents.base import AgentContext
from decision_copilot.llm.client import DeepSeekClient


class PlannerAgent:
    name = "planner"

    def __init__(self, llm: DeepSeekClient):
        self.llm = llm

    def run(self, ctx: AgentContext, inputs: dict) -> dict:
        system = (
            "You are a planning agent for a multi-agent decision pipeline. "
            "Your job is to decide which analysis agents are required."
        )

        user = (
            f"Decision question:\n{ctx.question}\n\n"
            f"Context:\n{ctx.context or ''}\n\n"
            "Select required agents from this allowed set:\n"
            '["facts", "pro", "con", "risk"]\n\n'
            "Return a plan in json with:\n"
            '- required_agents: list of agent names\n'
            "- rationale: short string\n"
            "- constraints: list of short strings (optional)\n"
        )

        example = {
            "required_agents": ["facts", "pro", "con", "risk"],
            "rationale": "Need balanced analysis before synthesis.",
            "constraints": ["Keep it concise."]
        }

        out = self.llm.chat_json(
            system=system,
            user=user,
            example_json=example,
            required_keys=["required_agents", "rationale"],
        )

        # Normalize / guardrail
        allowed = {"facts", "pro", "con", "risk"}
        req = [a for a in (out.get("required_agents") or []) if a in allowed]
        if not req:
            req = ["facts", "pro", "con", "risk"]

        out["required_agents"] = req
        return out
