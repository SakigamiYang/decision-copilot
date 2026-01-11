# Decision Copilot – Usage Guide

This document explains how to configure, start, and use Decision Copilot from end to end.  
It is intended to be uploaded to GitHub as a standalone usage guide.

## 1. What is Decision Copilot?

Decision Copilot is a lightweight, backend-first decision analysis tool built around LLM-based agents and a fully persistent execution model.

A decision is processed through a fixed pipeline:

planner → facts → pros → cons → risks → synth → report

Key characteristics:

- CLI-driven (no frontend required)
- Fully persistent (SQLite-backed)
- Asynchronous execution (Redis + RQ)
- Explainable and reproducible
- Designed as a tool, not a demo

## 2. Requirements

### System Requirements

- Python 3.12 or newer
- Redis (local or via Docker)

### Installation

Install the project in editable mode so the CLI becomes available:

```bash
uv pip install -e .
```

After installation, the `decision-copilot` command should be available in your shell.

## 3. Configuration

### 3.1 Environment Variables

Decision Copilot is configured entirely through environment variables. A `.env` file is recommended for local development.

Required:

```dotenv
DEEPSEEK_API_KEY=your_api_key_here
```

Optional (defaults shown):

```dotenv
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

Database location (optional):

```dotenv
DECISION_COPILOT_DB=data/decision_copilot.sqlite3
```

### 3.2 .env Files

- `.env`: local configuration file; must **not** be committed to GitHub.
- `.env.sample`: example configuration file; safe to commit.

Ensure `.env` is included in `.gitignore`.

## 4. Database Initialization

Before using Decision Copilot, initialize the SQLite database:

```bash
decision-copilot init-db
```

Expected behavior:

- The database file is created if it does not exist.
- Tables are created.
- No output errors.

This step is required only once (or after deleting the database file).

## 5. Starting the Worker

Decision Copilot executes agents asynchronously using Redis and RQ.

### 5.1 Start Redis

Using Docker:

```bash
docker run -d --name redis -p 6379:6379 redis:8-alpine
```

Ensure Redis is reachable on `localhost:6379`.

### 5.2 Start the Worker

In a separate terminal, start the worker process:

```bash
uv run python scripts/worker.py
```

Important notes:

- The worker uses RQ `SimpleWorker` (no forking).
- This avoids macOS fork-related crashes.
- Keep this process running while executing decisions.

## 6. Basic Workflow

### Step 1: Create a Decision

```bash
decision-copilot create "Should I use RQ SimpleWorker for local development on macOS?" \
  --context "I want to avoid fork-related crashes while testing async workflows."
```

Output:

```terminaloutput
<decision_id>
```

### Step 2: Start a Decision Run

```bash
decision-copilot run <decision_id>
```

This enqueues the planner and downstream agents.

Output:

```terminaloutput
<decision_run_id>
```

### Step 3: Monitor Status

```bash
decision-copilot status <decision_id>
```

This returns a JSON snapshot containing:

- Decision status
- Latest run status
- Per-agent execution state

## 7. CLI Commands

### List Decisions

```bash
decision-copilot list
```

Filter by status:

```bash
decision-copilot list --status done
```

Output format:

```terminaloutput
<id>    <status>    <question>
```

### Explain Execution

```bash
decision-copilot explain <decision_id>
```

Shows:

- Agent execution order
- Per-agent status
- Structured agent outputs

This command does **not** trigger any LLM calls.

### View Final Report (JSON)

```bash
decision-copilot report <decision_id>
```

Outputs the structured decision report produced by the `synth` agent.

### Export Report (Markdown)

Print to standard output:

```bash
decision-copilot export <decision_id> --format markdown
```

Write to a file:

```bash
decision-copilot export <decision_id> --format markdown --output report.md
```

The exported Markdown includes:

- Question and context
- Facts, pros, cons, and risks as bullet lists
- Final recommendation, rationale, and next steps

## 8. Agent Output Contracts (Summary)

Facts, Pros, Cons, and Risks agents all use the same strict output structure:

```json
{
  "items": [
    "One concise statement",
    "Another concise statement"
  ]
}
```

This guarantees:

- Stable rendering
- Predictable downstream processing
- Explainable results

The Synth agent produces a structured decision object containing:

- recommendation
- confidence
- rationale
- key_tradeoffs
- next_steps
- open_questions

## 9. Execution Model

- All agent outputs are persisted in SQLite.
- No in-memory orchestration state is required.
- Decisions and runs can be inspected after completion.
- The system is restart-safe and reproducible.

## 10. Troubleshooting

### Worker Runs but Nothing Happens

- Ensure Redis is running.
- Ensure the worker process is active.

### Agent Failure

- Run `decision-copilot status <id>`.
- Inspect worker logs for error details.

### LLM Errors

- Verify `DEEPSEEK_API_KEY`.
- Check network connectivity.
