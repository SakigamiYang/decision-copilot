# Agent Contracts

This document defines the output contracts for Decision Copilot agents.

These contracts are intentionally strict to ensure stable downstream processing, rendering, and explainability.

## 1. General Rules (All Agents)

Unless explicitly stated otherwise, all agents MUST follow these rules:

- Output MUST be valid JSON.
- Output MUST be a single JSON object (not an array).
- Output MUST NOT include markdown, code fences, or natural-language wrapper text.
- Output MUST match the contract described for that agent.
- Keys MUST be spelled exactly as specified (case-sensitive).
- Values MUST be of the specified type.

If an agent cannot comply, it should still return valid JSON that matches the required structure, using empty
arrays/strings where appropriate.

## 2. Shared Contracts

### 2.1 List-Item Contract (facts, pro, con, risk)

Agents `facts`, `pro`, `con`, and `risk` MUST return exactly:

```json
{
  "items": [
    "<string>",
    "<string>"
  ]
}
```

Rules:

- The JSON object MUST have exactly one key: `items`.
- `items` MUST be a list of strings.
- Each string MUST be concise (max one sentence).
- Each string MUST contain a single idea.
- The agent MUST NOT add additional keys (no `summary`, no `severity`, no `likelihood`, etc.).

Rationale:

- Enables stable rendering as bullet lists.
- Makes outputs easy to diff and test.
- Reduces schema drift and parsing failures.

## 3. Planner Agent

### 3.1 Purpose

The planner determines which downstream agents are required for this decision run.

### 3.2 Contract

Planner MUST return:

```json
{
  "required_agents": [
    "facts",
    "pro",
    "con",
    "risk"
  ]
}
```

Rules:

- `required_agents` MUST be a list of strings.
- Allowed values: `facts`, `pro`, `con`, `risk`.
- Unknown values MUST NOT be included.
- Duplicates MUST NOT be included.
- If the planner is uncertain, it should default to all allowed agents.

Notes:

- This contract keeps orchestration logic deterministic.
- The orchestrator may normalize/fallback if output is invalid.

## 4. Synth Agent

### 4.1 Purpose

Synth produces the final structured decision report by combining:

- decision question and context
- outputs from facts/pro/con/risk agents

### 4.2 Contract

Synth MUST return a JSON object with the following keys:

```json
{
  "recommendation": "<string>",
  "confidence": "<string>",
  "rationale": "<string>",
  "key_tradeoffs": [
    "<string>",
    "<string>"
  ],
  "next_steps": [
    "<string>",
    "<string>"
  ],
  "open_questions": [
    "<string>",
    "<string>"
  ]
}
```

Key rules:

- `recommendation`: string, concise final stance (e.g., "go", "no-go", "conditional_go").
- `confidence`: string, one of: `low`, `medium`, `high`.
- `rationale`: string, short narrative summary (multiple sentences allowed).
- `key_tradeoffs`: list of strings.
- `next_steps`: list of strings.
- `open_questions`: list of strings.

Additional rules:

- All lists MUST contain strings only.
- Lists SHOULD contain 2–6 items where possible.
- The synth output MUST NOT include markdown.
- The synth output MUST NOT include any extra keys (to keep export stable).

## 5. Error Handling and Empty Outputs

Agents should be robust under missing context or uncertain inputs.

### 5.1 Empty but Valid Outputs

If an agent cannot find relevant items, it should return a valid structure:

For list-item agents:

```json
{
  "items": []
}
```

For synth:

```json
{
  "recommendation": "conditional_go",
  "confidence": "low",
  "rationale": "Insufficient information to make a high-confidence recommendation.",
  "key_tradeoffs": [],
  "next_steps": [],
  "open_questions": [
    "What additional context is required?"
  ]
}
```

## 6. Contract Compatibility Notes

The CLI export renderer expects:

- facts/pro/con/risk outputs to follow the `{"items": [...]}` structure.
- synth output to contain the documented keys.

If you modify contracts, you must update:

- `decision_copilot/cli_commands/export.py` (rendering logic)
- any tests or validation logic
- any orchestration normalization rules (planner)

## 7. Versioning Guidance (Recommended)

If contracts evolve, add a version field at the orchestration or run level (not per agent output) to avoid schema drift:

- `DecisionRun.mode` can be used to identify contract versions (e.g., `contract_v1`).
- Alternatively, add `contract_version` to `DecisionRun` if needed.

The current contract set in this document is considered `v1`.