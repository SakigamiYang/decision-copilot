# coding: utf-8
from decision_copilot.agents.base import AgentContext
from decision_copilot.llm.client import DeepSeekClient


class ProAgent:
    """
    ProAgent lists concrete benefits and upside of a decision.

    Output contract (strict):
    {
      "items": [
        "<concise benefit statement>",
        ...
      ]
    }
    """

    name = "pro"

    def __init__(self, llm: DeepSeekClient):
        self.llm = llm

    def run(self, ctx: AgentContext, inputs: dict) -> dict:
        system = (
            "You analyze the benefits and upside of a decision.\n\n"
            "Rules:\n"
            "- Output valid JSON only\n"
            "- The JSON object MUST have exactly one key: 'items'\n"
            "- 'items' MUST be a list of strings\n"
            "- Each item MUST describe one concrete benefit\n"
            "- Each item MUST be concise (max 1 sentence)\n"
            "- Do NOT include explanations, titles, or impact levels\n"
            "- Do NOT include generic marketing language\n"
            "- Do NOT include recommendations\n"
        )

        user = (
            f"Decision question:\n{ctx.question}\n\n"
            f"Context:\n{ctx.context or ''}\n\n"
            "List the concrete benefits of this decision."
        )

        example = {
            "items": [
                "Using SimpleWorker avoids macOS fork-related crashes.",
                "Running jobs in-process simplifies debugging and observability.",
                "The setup reduces infrastructure complexity during local development.",
            ]
        }

        return self.llm.chat_json(
            system=system,
            user=user,
            example_json=example,
            required_keys=["items"],
        )
