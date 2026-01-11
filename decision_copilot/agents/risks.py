# coding: utf-8
from decision_copilot.agents.base import AgentContext
from decision_copilot.llm.client import DeepSeekClient


class RiskAgent:
    """
    RiskAgent lists potential risks and failure modes.

    Output contract (strict):
    {
      "items": [
        "<concise risk statement>",
        ...
      ]
    }
    """

    name = "risk"

    def __init__(self, llm: DeepSeekClient):
        self.llm = llm

    def run(self, ctx: AgentContext, inputs: dict) -> dict:
        system = (
            "You identify potential risks and failure modes of a decision.\n\n"
            "Rules:\n"
            "- Output valid JSON only\n"
            "- The JSON object MUST have exactly one key: 'items'\n"
            "- 'items' MUST be a list of strings\n"
            "- Each item MUST describe one realistic risk\n"
            "- Each item MUST be concise (max 1 sentence)\n"
            "- Do NOT include likelihood or impact scores\n"
            "- Do NOT include mitigation strategies\n"
            "- Do NOT include recommendations\n"
        )

        user = (
            f"Decision question:\n{ctx.question}\n\n"
            f"Context:\n{ctx.context or ''}\n\n"
            "List the main risks associated with this decision."
        )

        example = {
            "items": [
                "In-process execution may mask race conditions that appear under true concurrency.",
                "Long-running tasks could block the worker and delay other jobs.",
                "Unexpected side effects may persist across tasks within the same process.",
            ]
        }

        return self.llm.chat_json(
            system=system,
            user=user,
            example_json=example,
            required_keys=["items"],
        )
