# Architecture

This document describes the system architecture of Decision Copilot, including its core components, data flow, and design rationale.

## 1. Goals and Non-Goals

### Goals

- Provide a reproducible decision analysis pipeline driven by LLM-based agents.
- Persist all intermediate and final artifacts for traceability and explainability.
- Support asynchronous execution via a queue/worker model.
- Keep the user interface simple (CLI-first).

### Non-Goals

- No web frontend or SPA.
- No complex workflow engine or distributed orchestration framework.
- No tight coupling to a specific LLM provider (DeepSeek is the current implementation).

## 2. High-Level Architecture

Decision Copilot is composed of four layers:

- CLI Layer: user entry points and output formatting.
- Service Layer: domain operations and orchestration triggers.
- Execution Layer: asynchronous job execution using Redis + RQ.
- Persistence Layer: SQLite database for decisions, runs, and agent outputs.

Core technologies:

- SQLite for persistence
- Redis for message queue backend
- RQ for task scheduling and worker execution
- DeepSeek as the LLM provider (via `DeepSeekClient`)

## 3. Runtime Components

### 3.1 CLI

The `decision-copilot` CLI is the primary interface. It is responsible for:

- Creating decisions
- Starting runs
- Reading status snapshots and reports
- Exporting reports in human-readable formats

The CLI is intentionally thin: it delegates domain logic to `DecisionService` and reads results from the database.

### 3.2 Services

`DecisionService` is the main entry point for domain operations. Typical responsibilities:

- Create a `Decision`
- Create a `DecisionRun`
- Trigger orchestration start
- Build read models for `status`, `report`, and `explain`

The service layer is the bridge between CLI and orchestration/execution.

### 3.3 Orchestrator

The orchestrator implements DB-driven orchestration. It is responsible for:

- Starting a run by enqueuing the planner agent.
- After planner completes, reading planner output to determine required downstream agents.
- Enqueuing downstream agents (facts/pro/con/risk) in parallel.
- Enqueuing synth after all required agents finish.
- Performing fail-fast transitions when required agents fail.

Important property:

- Orchestration state is derived from database state, not in-memory state.

This makes the workflow restart-safe and inspectable.

### 3.4 Queue + Worker (RQ)

RQ is used to execute agent tasks asynchronously:

- Redis holds the job queue.
- The worker process fetches jobs and executes them.

On macOS, Decision Copilot runs the worker using RQ `SimpleWorker` to avoid fork-related crashes.

The queue layer is intentionally small:

- `queue/connection.py` provides queue/redis configuration.
- `queue/tasks.py` exposes task functions, primarily `run_agent(...)`.

### 3.5 Agents

Agents are specialized LLM prompts that produce structured JSON outputs.

Agents are designed to be:

- Deterministic in output schema (contract-first)
- Small and composable
- Independent (single responsibility)

Agents currently include:

- planner
- facts
- pro
- con
- risk
- synth

### 3.6 LLM Client

`DeepSeekClient` is the provider integration. It is responsible for:

- Calling DeepSeek chat completions
- Enforcing JSON-only output (via prompt constraints and response parsing)
- Returning Python dictionaries to agents

Configuration is provided via environment variables (typically loaded from `.env` at process start).

### 3.7 Persistence (SQLite)

SQLite persists all workflow state:

- Decisions and their final reports
- Runs and required agent lists
- Per-agent execution records including status, timing, output, and errors

The database is the source of truth for:

- Execution state transitions
- Explainability and audit trails
- Exported reports

## 4. Data Flow (End-to-End)

1. User creates a decision:
   - CLI → DecisionService → insert `Decision` row

2. User starts a run:
   - CLI → DecisionService → insert `DecisionRun`
   - DecisionService → Orchestrator.start(run_id)

3. Orchestrator enqueues planner:
   - Orchestrator → RQ enqueue `run_agent(run_id, "planner")`

4. Worker executes planner:
   - Task loads decision + run from DB
   - Calls PlannerAgent → persists output to `AgentRun`
   - Calls Orchestrator.on_agent_done(...)

5. Orchestrator fans out downstream agents:
   - Reads planner output → sets `DecisionRun.required_agents`
   - Enqueues facts/pro/con/risk (parallel)

6. Worker executes downstream agents:
   - Each agent writes output to its `AgentRun`
   - Orchestrator checks completion state after each agent finishes

7. Orchestrator enqueues synth:
   - Only after all required agents are DONE

8. Worker executes synth:
   - Loads downstream outputs
   - Calls SynthAgent → persists output
   - Orchestrator writes `Decision.final_report`, marks run/decision DONE

## 5. State Machine

### Decision Status

Typical states:

- queued (optional, if used)
- running
- done
- failed

### Run Status

Typical states:

- queued (optional, if used)
- running
- done
- failed

### Agent Status

Typical states:

- queued
- running
- done
- failed

Orchestrator performs fail-fast behavior:

- If any required agent fails, mark run and decision as FAILED.

## 6. Design Decisions

### 6.1 DB-Driven Orchestration

Rationale:

- Avoids fragile in-memory state
- Allows restart and recovery
- Enables explain and export features without recomputation

### 6.2 Strict Output Contracts

Rationale:

- Enables stable downstream processing
- Simplifies export rendering
- Makes results testable and comparable

### 6.3 CLI-First

Rationale:

- Eliminates frontend complexity
- Keeps iteration speed high
- Aligns with developer workflows

### 6.4 Minimal Abstraction

Rationale:

- MVP-friendly
- Easy to reason about
- Avoids premature complexity (no workflow engine, no web app)

## 7. Operational Notes

- `.env` is loaded at process startup (CLI and worker).
- Redis must be reachable by both CLI and worker.
- SQLite is a local persistence layer; for multi-worker concurrency or production usage, a server DB may be required.

## 8. Repository Structure (Conceptual)

Typical layout:

- `decision_copilot/`
  - `cli.py`
  - `cli_commands/`
  - `config.py`
  - `database.py`
  - `models.py`
  - `services/`
  - `orchestrator/`
  - `agents/`
  - `queue/`
  - `llm/`
- `scripts/worker.py`
- `docs/`
  - `usage.md`
  - `architecture.md`
  - `agnet-contracts.md`
- `.env.sample`
- `.gitignore`
