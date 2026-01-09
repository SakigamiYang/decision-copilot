# Decision Copilot (Multi-Agent, Auditable Decision Support)

Decision Copilot is a production-oriented practice project that demonstrates how to build a scalable, 
auditable multi-agent LLM application with a minimal front end. Users submit a decision question 
(optionally with context). The system orchestrates multiple specialized agents—Planner, Facts, Pro, Con, Risk, 
and Synthesizer—executed asynchronously via Dramatiq workers. Each agent produces structured outputs 
that are persisted for traceability, enabling replay, evaluation, and iterative improvement.

The backend is implemented with FastAPI for API endpoints and orchestration, Redis for job queueing and caching, 
and PostgreSQL for durable storage of decisions, agent runs, and final reports. An optional pgvector layer 
can be used to store embeddings for historical decision similarity and comparison. The front end uses Alpine.js 
and Bootstrap and intentionally remains lightweight: a submission page, a progress page (polling or streaming), 
and a final structured report page. The entire system is containerized with Docker Compose, 
with Caddy serving the static front end and reverse-proxying API traffic.

This repository focuses on practical engineering concerns that arise in real LLM systems: asynchronous execution, 
parallel multi-agent workflows, structured outputs, audit logs, failure handling and retries, cost/latency tracking, 
and clean separation between API, worker, and storage layers.