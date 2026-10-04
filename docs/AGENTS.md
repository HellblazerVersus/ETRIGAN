# AGENTS.md — Instructions & Conventions for Coding Agents (Claude & Developers)

Welcome to **ETRIGAN (DEMO-PROJECT)**. This file dictates non-negotiable architectural rules, coding conventions, and run commands for this repository.

---

## 1. Project Context & Mission

- **Problem Statement:** DEMO-PROJECT (Mangalore Refinery and Petrochemicals Limited - ACME).
- **Core Product:** Sovereign On-Premise Agentic AI Workbench running open-weight models locally with zero external network access, multi-model routing, agentic tool execution, multimodal ingestion, real file deliverables (`.docx`/`.xlsx`), grounded local knowledge base, tamper-evident audit logs, and on-premise fine-tuning via **Soup**.
- **Deadline:** Tomorrow! Prototype must be robust, demoable, and runnable on consumer hardware.

---

## 2. Hardware Reality & Path Constraints

- **Host Machine:** Intel Iris Xe integrated graphics (NO CUDA, CPU inference).
- **RAM:** 15.4 GB total (~4 GB max per active model, max 2 models hot).
- **C: Drive Warning:** Very low free space (<2 GB).
  - **NEVER** save model weights, virtual environments, or large caches on `C:`.
  - Always set `OLLAMA_MODELS=D:\projects\SIH\models` (or `/mnt/d/projects/SIH/models`).
  - Virtual environment must be located on `D:`: `/mnt/d/projects/SIH/.venv`.
- **Primary Profile:** `venue` profile (CPU-friendly 1B–4B models: `llama3.2:1b`, `qwen2.5:3b`, `qwen2.5-coder:3b`, `nomic-embed-text`).

---

## 3. Non-Negotiable Rules

1. **ZERO EXTERNAL NETWORK REQUESTS AT RUNTIME:**
   - Never import OpenAI, Anthropic, HuggingFace Hub, Pinecone, LangChain-cloud, or Clerk SDKs.
   - All LLM calls must go through Ollama's local OpenAI-compatible endpoint (`http://localhost:11434/v1`).
   - Frontend must vendor all fonts (Inter) and icons (Lucide-React). DevTools network tab must show 0 remote requests.
2. **NO HEAVY AGENT FRAMEWORKS:**
   - Do NOT use LangChain or CrewAI as the core agent loop.
   - Hand-roll an explicit ~300-line Python agent loop in `app/agent/loop.py` using Pydantic v2 schemas (`Plan`, `PlanStep`).
3. **STORAGE & SEARCH (ZERO DAEMON OVERHEAD):**
   - Use SQLite (`etrigan.db`) in WAL mode.
   - Lexical search: SQLite FTS5.
   - Vector search: In-memory NumPy cosine similarity over 768-dim embeddings stored as BLOBs in SQLite.
4. **SANDBOX DUAL BACKEND:**
   - Docker if daemon is running (`network_mode: none`).
   - Hardened Subprocess fallback if Docker daemon is down (strips env vars, blocks `socket.socket` to throw `ConnectionError` on network attempts, 60s timeout).
5. **REAL DELIVERABLES:**
   - Model outputs typed JSON specs (`ApprovalNote`, `CalculationSheet`).
   - Deterministic Python generators (`python-docx`, `openpyxl`) render real `.docx` and `.xlsx` files with live formulas and provenance footers.
6. **SOVEREIGN FINE-TUNING VIA SOUP:**
   - Shipped in `config/soup.yaml`. Showcases how ACME can fine-tune 8B models on a 4GB laptop GPU using Soup's layer streaming without cloud GPUs.

---

## 4. Repository Structure

```
/mnt/d/projects/SIH/
├── BUILD_SPEC.md              # Target engineering specification
├── PLAN.md                    # 36-hour prototype plan & checklist
├── AGENTS.md                  # This file
├── config/
│   ├── models.yaml            # Model registry & routing rules
│   ├── soup.yaml              # Soup fine-tuning recipe for ACME
│   └── policy.yaml            # Workspace clearances & tool policies
├── app/                       # FastAPI orchestrator
│   ├── main.py                # App entrypoint & SSE stream endpoints
│   ├── router/                # Task classification & model selection
│   ├── agent/                 # Hand-rolled loop: plan -> act -> observe -> repair
│   ├── tools/                 # Tool implementations (fs, code, sheet, docs)
│   ├── ingest/                # PyMuPDF + RapidOCR / VLM document parser
│   ├── kb/                    # SQLite FTS5 + NumPy cosine hybrid RAG
│   ├── deliver/               # python-docx and openpyxl generators
│   ├── audit/                 # Append-only SHA-256 hash-chained audit log
│   └── store/                 # SQLite database connection & schema
├── web/                       # Vite + React 18 + TS + Tailwind frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx
│   │   │   ├── PlanPanel.tsx
│   │   │   ├── RouterPanel.tsx
│   │   │   ├── SourcesPanel.tsx
│   │   │   ├── ArtifactsPanel.tsx
│   │   │   ├── FineTuningView.tsx   # Soup visualizer & YAML viewer
│   │   │   └── SovereigntyBar.tsx   # Live 0-egress status bar
│   │   └── App.tsx
├── seed/                      # Sample ACME documents & inspection CSVs
└── run.sh / run.ps1           # Single command to launch prototype
```

---

## 5. Development Commands

### Python Environment Setup
```bash
cd /mnt/d/projects/SIH
uv venv --python 3.11 .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic python-docx openpyxl pymupdf httpx numpy
```

### Frontend Setup
```bash
cd /mnt/d/projects/SIH/web
npm install
npm run dev
```

### Start Orchestrator
```bash
cd /mnt/d/projects/SIH
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
