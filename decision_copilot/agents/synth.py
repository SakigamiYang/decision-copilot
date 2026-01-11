# coding: utf-8
from decision_copilot.agents.base import AgentContext
from decision_copilot.llm.client import DeepSeekClient


class SynthAgent:
    name = "synth"

    def __init__(self, llm: DeepSeekClient):
        self.llm = llm

    def run(self, ctx: AgentContext, inputs: dict) -> dict:
        system = (
            "You are a decision synthesis agent. "
            "You must produce a structured recommendation using the provided inputs."
        )

        facts = inputs.get("facts", {})
        pros = inputs.get("pro", {})
        cons = inputs.get("con", {})
        risks = inputs.get("risk", {})

        user = (
            f"Decision question:\n{ctx.question}\n\n"
            f"Context:\n{ctx.context or ''}\n\n"
            f"Facts json:\n{facts}\n\n"
            f"Pros json:\n{pros}\n\n"
            f"Cons json:\n{cons}\n\n"
            f"Risks json:\n{risks}\n\n"
            "Return json with:\n"
            "- recommendation: one of [go, no_go, conditional_go, gather_more_info]\n"
            "- confidence: one of [low, medium, high]\n"
            "- rationale: short paragraph\n"
            "- key_tradeoffs: list of strings\n"
            "- next_steps: list of strings\n"
            "- open_questions: list of strings\n"
        )

        example = {
            "recommendation": "conditional_go",
            "confidence": "medium",
            "rationale": "Short rationale grounded in facts and tradeoffs.",
            "key_tradeoffs": ["Tradeoff 1", "Tradeoff 2"],
            "next_steps": ["Step 1", "Step 2"],
            "open_questions": ["Question 1"]
        }

        return self.llm.chat_json(
            system=system,
            user=user,
            example_json=example,
            required_keys=["recommendation", "confidence", "rationale", "key_tradeoffs", "next_steps",
                           "open_questions"],
        )
