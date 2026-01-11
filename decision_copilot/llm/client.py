# coding: utf-8
import os
from dataclasses import dataclass
from typing import Any, Optional

import orjson
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params import ResponseFormatJSONObject


@dataclass(frozen=True)
class DeepSeekConfig:
    base_url: str = os.environ.get("DEEPSEEK_BASE_URL")
    api_key: Optional[str] = os.environ.get("DEEPSEEK_API_KEY")
    model: str = os.environ.get("DEEPSEEK_MODEL")


class DeepSeekClient:
    """
    DeepSeek API is OpenAI-compatible. We use the OpenAI Python SDK with base_url override.
    This client provides:
      - text completion (non-structured)
      - strict JSON completion (response_format=json_object) + parsing + basic validation
    """

    def __init__(self, cfg: Optional[DeepSeekConfig] = None):
        self.cfg = cfg or DeepSeekConfig()
        self._client = None

        if not self.cfg.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    def _get_client(self):
        if self._client is not None:
            return self._client

        self._client = OpenAI(api_key=self.cfg.api_key, base_url=self.cfg.base_url)
        return self._client

    def chat_text(self, system: str, user: str, *, model: Optional[str] = None) -> str:
        client = self._get_client()
        resp = client.chat.completions.create(
            model=model or self.cfg.model,
            messages=[
                ChatCompletionSystemMessageParam(content=system, role="system"),
                ChatCompletionUserMessageParam(content=user, role="user"),
            ],
        )
        return (resp.choices[0].message.content or "").strip()

    def chat_json(
            self,
            system: str,
            user: str,
            *,
            example_json: dict[str, Any],
            required_keys: Optional[list[str]] = None,
            model: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Enforces JSON-only output via DeepSeek JSON Output mode:
          - response_format={"type": "json_object"}
          - prompt includes the word 'json' and provides an example
        Returns parsed dict. Raises ValueError if invalid.
        """
        required_keys = required_keys or []

        system_with_example = (
            f"{system}\n\n"
            "You must output valid JSON only.\n"
            "The output MUST be a single JSON object and nothing else.\n"
            "Here is an example JSON output format:\n"
            f"{orjson.dumps(example_json, option=orjson.OPT_INDENT_2)}\n"
        )

        user_with_json_hint = (
            f"{user}\n\n"
            "Remember: output must be JSON."
        )

        client = self._get_client()
        resp = client.chat.completions.create(
            model=model or self.cfg.model,
            messages=[
                ChatCompletionSystemMessageParam(content=system_with_example, role="system"),
                ChatCompletionUserMessageParam(content=user_with_json_hint, role="user"),
            ],
            response_format=ResponseFormatJSONObject(type="json_object"),
        )

        content = (resp.choices[0].message.content or "").strip()
        if not content:
            raise ValueError("Empty JSON content returned by model.")

        try:
            obj = orjson.loads(content)
        except orjson.JSONDecodeError as e:
            raise ValueError(f"Model did not return valid JSON. Raw content: {content[:4000]}") from e

        if not isinstance(obj, dict):
            raise ValueError(f"Model JSON output is not an object. Got type={type(obj)}")

        missing = [k for k in required_keys if k not in obj]
        if missing:
            raise ValueError(f"Model JSON output missing required keys: {missing}. Got keys={list(obj.keys())}")

        return obj
