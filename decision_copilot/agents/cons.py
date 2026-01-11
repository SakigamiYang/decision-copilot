# coding: utf-8
from decision_copilot.agents.base import AgentContext
from decision_copilot.llm.client import DeepSeekClient


class ConAgent:
    """
    ConAgent lists concrete downsides, costs, and negative trade-offs.

    Output contract (strict):
    {
      "items": [
        "<concise downside statement>",
        ...
      ]
    }
    """

    name = "con"

    def __init__(self, llm: DeepSeekClient):
        self.llm = llm

    def run(self, ctx: AgentContext, inputs: dict) -> dict:
        system = (
            "You analyze downsides, costs, and negative trade-offs of a decision.\n\n"
            "Rules:\n"
            "- Output valid JSON only\n"
            "- The JSON object MUST have exactly one key: 'items'\n"
            "- 'items' MUST be a list of strings\n"
            "- Each item MUST describe one concrete downside or cost\n"
            "- Each item MUST be concise (max 1 sentence)\n"
            "- Do NOT include severity levels or scores\n"
            "- Do NOT include explanations or mitigation\n"
            "- Do NOT include recommendations\n"
        )

        user = (
            f"Decision question:\n{ctx.question}\n\n"
            f"Context:\n{ctx.context or ''}\n\n"
            "List the concrete downsides or costs of this decision."
        )

        example = {
            "items": [
                "Running all jobs in-process reduces isolation between tasks.",
                "Errors in one job may affect the stability of the worker process.",
                "The approach may hide concurrency issues that appear in forked execution.",
            ]
        }

        return self.llm.chat_json(
            system=system,
            user=user,
            example_json=example,
            required_keys=["items"],
        )
