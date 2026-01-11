# coding: utf-8
from decision_copilot.agents.base import AgentContext
from decision_copilot.llm.client import DeepSeekClient


class FactsAgent:
    """
    FactsAgent produces neutral, verifiable statements only.

    Output contract (strict):
    {
      "items": [
        "<short factual statement>",
        ...
      ]
    }
    """

    name = "facts"

    def __init__(self, llm: DeepSeekClient):
        self.llm = llm

    def run(self, ctx: AgentContext, inputs: dict) -> dict:
        system = (
            "You are a factual analyst.\n"
            "Your task is to list neutral, verifiable facts relevant to the decision.\n\n"
            "Rules:\n"
            "- Output valid JSON only\n"
            "- The JSON object MUST have exactly one key: 'items'\n"
            "- 'items' MUST be a list of strings\n"
            "- Each item MUST be a short factual statement (max 1 sentence)\n"
            "- Do NOT include opinions, recommendations, or speculation\n"
            "- Do NOT include assumptions or unknowns\n"
            "- Do NOT include explanations or markdown\n"
        )

        user = (
            f"Decision question:\n{ctx.question}\n\n"
            f"Context:\n{ctx.context or ''}\n\n"
            "List only concrete facts that are relevant to this decision."
        )

        example = {
            "items": [
                "RQ can execute jobs in-process using SimpleWorker without forking.",
                "macOS may crash when Python processes fork after Objective-C initialization.",
            ]
        }

        return self.llm.chat_json(
            system=system,
            user=user,
            example_json=example,
            required_keys=["items"],
        )
