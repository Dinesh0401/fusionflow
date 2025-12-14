# VocaVerse Developer Setup

## Prerequisites

- Node.js 20+
- Python 3.11+
- FFmpeg (for audio transcoding, optional for dev)

## Backend (FastAPI)

1. Create virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. Configure environment variables by copying `.env.example` (to be provided) into `.env`.
3. Ensure the `data/` directory exists for the SQLite decision ledger (created by default in this repo).
4. Run development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Optional: adjust `ML_RISK_THRESHOLD` and `LLM_CONFIDENCE_THRESHOLD` in `.env` to tune automation gating.
6. For contract fuzz tests, install dev dependencies: `pip install -r requirements-dev.txt` and run `pytest`.

## Offline Evaluation Pipeline

- Create an OTLP collector endpoint (optional) and set `OTEL_EXPORTER_ENDPOINT` to stream telemetry.
- Export provider metrics: `python -m app.scripts.export_provider_report --format json`.
- Backfill prompt hashes for legacy records if upgrading: `python -m app.scripts.backfill_prompt_hash`.
- Use the helpers in `app.evaluation` to compute calibration, gate effectiveness, and prompt-hash drift before adjusting thresholds.

## Frontend (React + Vite)

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start development server:
   ```bash
   npm run dev
   ```
3. Access the UI at http://localhost:5173.

## MCP Integration Stubs

- Backend targets MCP server at `http://localhost:8400` by default.
- Update `MCP_SERVER_URL` in `.env` once the MCP server implementation is available.

## Next Steps

- Flesh out speech pipeline with real STT provider.
- Implement MCP server routes under `mcp/`.
- Expand docs with architecture and sequence diagrams.
- Build analytics on top of the decision ledger for confidence calibration.
