 # VocaVerse – MCP-Driven AI Visual English Communication Platform

## Repository Structure

```
backend/      # FastAPI services, MCP integration, tool handlers
frontend/     # React-based client with WebGL avatars and WebRTC audio
mcp/          # MCP server configuration, schemas, and adapters
docs/         # Architecture diagrams, design notes, ADRs
```

## Getting Started

1. Refer to docs/ for architectural background and design decisions.
2. Bootstrap backend and frontend services using the provided scaffolding scripts (coming soon).
3. Configure MCP runtime components before enabling AI agents.
4. Review the decision ledger flow to understand how automation verdicts are persisted for auditability (see [docs/decision-ledger.md](docs/decision-ledger.md)).
5. Analyze offline performance using the evaluation helpers and report template in [docs/evaluation/report.md](docs/evaluation/report.md).

LLM agents must comply with the contract documented in [docs/llm-contract.md](docs/llm-contract.md).

## Deterministic Decision Traceability
Prompt invocations are hashed before MCP dispatch, gate verdicts are persisted to the decision ledger, and the combination enables replaying any automation flow with a verifiable audit trail across providers and models.
