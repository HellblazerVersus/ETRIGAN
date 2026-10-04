# ETRIGAN — Sovereign On-Premise Agentic AI Workbench

**Build specification for an AI coding agent.**
Target: Smart India Hackathon 2026, problem statement **DEMO-PROJECT** (Mangalore Refinery and Petrochemicals Limited).

> **How to use this document.** Give it to a coding agent as the repo's `BUILD_SPEC.md`. Build strictly phase by phase. Do not begin a phase until the previous phase's acceptance criteria pass. Each phase ends with a demoable state — that is deliberate, because the demo is the deliverable.

---

## 0. What we are building, in one paragraph

A self-hosted AI workbench that runs entirely inside an organisation's own network on its own GPU, with **no external network calls at any point**. It serves multiple open-weight models at once and routes each task to the right one automatically. It behaves as an agent — it plans multi-step work, calls local tools (file I/O, sandboxed code execution, document search, spreadsheet operations), and iterates until the task is done. It reads scanned PDFs, handwritten notes, engineering drawings and photographs using on-device OCR and vision models. It produces **real files** — Word, Excel, PowerPoint, source code, calculations with working shown — not chat replies. It grounds its answers in the organisation's own manuals, SOPs and correspondence through a local knowledge base, with citations. And it proves the sovereignty claim visibly, through a live network monitor and a tamper-evident audit log, rather than merely asserting it.

**Name:** Etrigan (self-rule). Rename freely; keep it short and say it in the first ten seconds of the pitch.

### The seven capabilities the problem statement demands

Every one of these must be visibly demonstrable. They map 1:1 to acceptance criteria later.

| # | Requirement (from the PS) | Where it is satisfied |
|---|---|---|
| R1 | Multiple open-weight models served at once, auto-selected per task | Phase 1 — model registry + router |
| R2 | New models addable later without redesign | Phase 1 — YAML registry, hot-add CLI |
| R3 | Agentic: plans, calls local tools, iterates | Phase 2 — agent loop + plan panel |
| R4 | Multimodal: scanned PDFs, handwriting, drawings, photos | Phase 3 — ingest pipeline + VLM |
| R5 | Real deliverables (Word/Excel/PPT/code/calculations) | Phase 4 — artifact generators |
| R6 | Grounded in local manuals/SOPs via local KB | Phase 3 — hybrid RAG with citations |
| R7 | **Provable** zero external calls | Phase 5 — sovereignty monitor + audit chain |

R7 is the one that wins. Everyone will claim air-gapped. Almost nobody will *prove* it on stage.

---

## 1. Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  BROWSER (LAN only) — Next.js UI                                     │
│  Chat · Plan/Trace · Artifacts · Sources · Router log · Sovereignty  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ SSE + REST (no external assets)
┌───────────────────────────────▼──────────────────────────────────────┐
│  ORCHESTRATOR — FastAPI (Python 3.11)                                │
│                                                                      │
│  ┌────────────┐   ┌──────────────┐   ┌───────────────────────────┐   │
│  │  Router    │──▶│  Agent Loop  │──▶│  Tool Registry            │   │
│  │ classify   │   │ plan→act→    │   │  fs · code · docs · sheet │   │
│  │ → pick     │   │ observe→     │   │  ocr · vision · deliver   │   │
│  │   model    │   │ iterate      │   │                           │   │
│  └─────┬──────┘   └──────┬───────┘   └────────────┬──────────────┘   │
│        │                 │                        │                  │
│  ┌─────▼─────────────────▼────────────────────────▼──────────────┐   │
│  │  Audit Chain — every model call, tool call, file touched      │   │
│  │  hash-chained, append-only                                    │   │
│  └───────────────────────────────────────────────────────────────┘   │
└───┬───────────────┬────────────────┬───────────────────┬─────────────┘
    │               │                │                   │
┌───▼──────┐  ┌─────▼──────┐  ┌──────▼───────┐  ┌────────▼──────────┐
│ Inference│  │ Postgres   │  │ Sandbox      │  │ Sovereignty       │
│ vLLM /   │  │ + pgvector │  │ Docker       │  │ Monitor (sidecar) │
│ Ollama   │  │ KB + audit │  │ network:none │  │ nftables log tail │
│ (OpenAI- │  │ + sessions │  │ ro rootfs    │  │ → live WS feed    │
│  compat) │  │            │  │ cpu/mem caps │  │                   │
└──────────┘  └────────────┘  └──────────────┘  └───────────────────┘

        ══════ DOCKER NETWORK: egress DENY by default ══════
```

### Design rules that are not negotiable

1. **Everything talks OpenAI-compatible HTTP to the inference layer.** The orchestrator must never import a model-specific SDK. This is what makes R2 (add a model later) a config change rather than a refactor.
2. **No external asset at runtime.** No CDN, no Google Fonts, no remote icon set, no telemetry, no `pip install` at runtime. Self-host fonts and icons in the repo. A judge opening devtools must see zero third-party requests.
3. **Every tool call is logged before it executes**, with its arguments, and after, with its result hash. The audit chain is written synchronously, not best-effort.
4. **The sandbox has no network.** `network_mode: none`, read-only root filesystem, writable `/work` only, CPU and memory caps, hard timeout.
5. **Small, explicit agent loop. No heavyweight agent framework.** LangGraph/CrewAI-style abstractions hide the mechanism, behave unpredictably on open-weight models, and cannot be read by a judge in thirty seconds. Hand-roll roughly 300 lines with Pydantic-typed tool schemas.

---

## 2. Technology choices

The workbench is architected with a **dual profile**:
- **Venue Profile (Demo / Weak PC):** Sized for integrated graphics (e.g. Intel Iris Xe / 4GB VRAM / CPU inference) and zero-daemon instant startup.
- **Server Profile (Production Enterprise):** Sized for multi-GPU servers (A100 / RTX 4090) with high concurrency.

| Layer | Venue Choice (Demo / Weak PC) | Server Choice (Production) | Why this design |
|---|---|---|---|
| Inference server | **Ollama** (`:11434/v1`) | **vLLM** (`:8000/v1`) | Both expose OpenAI-compatible HTTP. Never import a vendor SDK. |
| Orchestrator | **Python 3.11/3.12 + FastAPI + Uvicorn** | Same | Native async, SSE streaming, document/OCR ecosystem. |
| Validation | **Pydantic v2** | Same | Strict JSON schemas for plans, tools, router decisions. |
| Datastore | **SQLite (`etrigan.db`) + FTS5** | **PostgreSQL 16 + pgvector** | SQLite needs zero daemons and runs in WAL mode; Postgres scales to enterprise. |
| Vector search | **In-memory NumPy Cosine** | **pgvector (HNSW)** | At <1,000 chunks, NumPy cosine is sub-millisecond on CPU. |
| Embeddings | **`nomic-embed-text`** (274 MB via Ollama) | **BGE-M3** (2.2 GB) | Nomic takes ~80ms on CPU vs BGE's ~3s on CPU. |
| Ingest & OCR | **PyMuPDF + RapidOCR (ONNX) + VLM** | **PaddleOCR + VLM** | RapidOCR runs via ONNX runtime without heavy CUDA dependencies. |
| Deliverables | **python-docx, openpyxl, python-pptx** | Same | Real downloadable office files with live formulas. |
| Frontend | **Vite + React 18 + TS + Tailwind + shadcn** | Same | Fast HMR, no SSR complexity, vendored offline fonts & Lucide icons. |
| Sandbox | **Dual Backend: Docker or Subprocess** | **Docker (`network_mode: none`)** | Subprocess fallback strips sockets and env for machines without Docker daemon. |
| Domain Fine-Tuning | **Soup (`soup-cli`)** | Same | Single-YAML QLoRA with layer streaming — enables 8B fine-tuning on a 4GB laptop GPU. |

### Explicitly rejected

- **Any hosted service** — Supabase, Pinecone, Clerk, Vercel, OpenAI/Anthropic APIs. One of these in code destroys the entire pitch.
- **LangChain / LlamaIndex as the backbone.** Fine to borrow a document loader; hand-roll the agent loop in ~300 lines of clear Python.
- **Remote CDNs / External fonts.** Devtools must verify 100% offline localhost traffic.

---

## 3. Models

Target four functional roles. The **Venue Profile** is strictly tuned for resource-constrained presentation hardware (Intel Iris Xe / integrated GPU / 4-16 GB RAM / CPU inference), while the **Server Profile** targets dedicated enterprise multi-GPU nodes.

| Role | Needs | Venue Profile (CPU / Integrated GPU / ~7.5 GB total) | Server Profile (16GB+ VRAM) |
|---|---|---|---|
| `classifier` | Fast JSON task classification & routing | **`llama3.2:1b`** (1.3 GB, JSON schema constrained) | `llama3.1:8b` |
| `general` | Drafting, summarising, planning | **`qwen2.5:3b`** or **`qwen3:4b`** (2.6 GB) | `qwen2.5:32b` or `llama3.3:70b` |
| `code` | Code generation & tool calling | **`qwen2.5-coder:3b`** (1.9 GB) | `qwen2.5-coder:32b` |
| `vision` | Scans, drawings, handwriting, P&IDs | **`qwen2.5vl:3b`** (3.2 GB) + RapidOCR fallback | `qwen2.5vl:72b` |
| `embed` | Grounded KB embeddings | **`nomic-embed-text`** (274 MB, ~80ms on CPU) | `BGE-M3` (2.2 GB) |

The PS explicitly permits smaller open-weight models if 120B-class hardware is unavailable at the venue. Ship **two profiles** (`profiles/venue.yaml`, `profiles/server.yaml`) and state on stage:
> *"We are demonstrating live on the venue profile — running completely on integrated graphics without a discrete GPU. The enterprise server profile is one config flag away."*

This turns venue hardware constraints into tangible evidence of disciplined software engineering.

---

## 4. Component specifications

### 4.1 Model registry and router (R1, R2)

`config/models.yaml` — adding a model is appending a block here plus pulling the weights. Nothing else.

```yaml
models:
  - id: general-8b
    endpoint: http://inference:11434/v1
    served_name: <model-name>
    roles: [general, summarize, longdoc]
    context: 32768
    vram_gb: 6
    speed: fast
    supports: { tools: true, vision: false, json_mode: true }

  - id: coder-14b
    endpoint: http://inference:11434/v1
    served_name: <model-name>
    roles: [code, refactor, sql]
    context: 32768
    vram_gb: 10
    speed: medium
    supports: { tools: true, vision: false, json_mode: true }

  - id: vision-7b
    endpoint: http://inference:11434/v1
    served_name: <model-name>
    roles: [vision, ocr_assist, drawing]
    context: 16384
    vram_gb: 8
    speed: medium
    supports: { tools: false, vision: true, json_mode: true }

routing:
  default_role: general
  vram_budget_gb: 12
  rules:
    - if: { has_image: true }              then_role: vision
    - if: { task_class: code }             then_role: code
    - if: { task_class: calculation }      then_role: reasoning
    - if: { input_tokens_gt: 16000 }       then_role: longdoc
```

**Routing procedure** (`app/router/route.py`):

1. **Signal extraction** — deterministic, no model call: does the input carry images or a scanned PDF? estimated input tokens? file extensions attached? explicit user override?
2. **Task classification** — a small local model returns strict JSON `{task_class, confidence, rationale}` over a fixed label set: `code | calculation | document_qa | summarize | drafting | vision | data_analysis`. Cache by prompt hash.
3. **Candidate filter** — models whose `roles` include the required role, whose `context` fits the input, and whose `vram_gb` fits the remaining budget.
4. **Score and pick** — prefer role specificity, then speed, then smaller VRAM. Deterministic tie-break so demos are reproducible.
5. **Emit a `RoutingDecision`** and stream it to the UI *before* generation starts.

```python
class RoutingDecision(BaseModel):
    task_class: str
    chosen_model: str
    considered: list[str]
    reasons: list[str]        # "input contains 3 page images → vision role required"
    confidence: float
    fallback_used: bool
```

**The router panel is a demo asset, not a debug view.** Judges must see, in plain English: *"Classified as `code` (0.91). Considered general-8b, coder-14b. Chose coder-14b because the task requires sandboxed execution and tool calling."* Then the next prompt routes somewhere else and they watch it switch. That single visual satisfies R1 more convincingly than any slide.

**Hot-add proof (R2):** a CLI — `etrigan model add --file new-model.yaml` — validates the block, appends to the registry, reloads without restarting the orchestrator, and the new model appears in the router panel. Do this live on stage. It takes fifteen seconds and it answers "what about next year's models?" permanently.

### 4.2 Agent loop (R3)

```
receive task
  └─ route → model
  └─ PLAN: model emits a typed Plan (steps, tool per step, success criterion)
  └─ render plan in UI immediately
  └─ for each step (max N, default 12):
        ├─ select tool + validate args against Pydantic schema
        ├─ write audit entry (pre)
        ├─ execute tool
        ├─ write audit entry (post, result hash)
        ├─ observe: model reviews the result
        └─ if step failed → repair (retry with the error, up to 2) or replan
  └─ VERIFY: model checks output against the plan's success criterion
  └─ DELIVER: produce artifacts, attach citations, close the audit chain
```

```python
class PlanStep(BaseModel):
    n: int
    intent: str                    # human-readable, shown in the UI
    tool: str | None
    args: dict | None
    success_criterion: str

class Plan(BaseModel):
    goal: str
    steps: list[PlanStep]
    deliverables: list[str]        # e.g. ["approval_note.docx"]
```

Implementation notes that matter with open-weight models:

- **Force JSON.** Use the inference server's grammar/JSON-schema constraint. Do not parse free text and hope.
- **One tool per step.** Parallel tool calls from small models are a reliability disaster.
- **Repair beats retry.** On a failed step, feed the *actual error text* back and ask for a corrected call — that loop is what makes it look intelligent on stage.
- **Replanning is a feature.** When a step fails twice, the agent revises the plan and the UI visibly redraws it. Judges read that as genuine agency. Script a demo task where this happens.
- **Hard caps:** max steps, max wall-clock, max tokens. An agent that spirals during a demo is worse than one that stops and explains.

### 4.3 Tools (R3)

All tools are Pydantic-schema'd, registered in one table, and individually permissioned per workspace.

| Tool | Signature | Notes |
|---|---|---|
| `fs.list` | `(path) -> entries` | Scoped to the workspace root. Path traversal rejected. |
| `fs.read` | `(path, range?) -> text` | Binary files route to the ingest pipeline instead. |
| `fs.write` | `(path, content) -> receipt` | Writes under `/work/out` only. |
| `code.run` | `(language, source, files?) -> {stdout, stderr, exit, artifacts}` | Docker, `network_mode: none`, read-only rootfs, `/work` writable, 2 CPU / 2 GB / 60 s. |
| `docs.search` | `(query, k, filters?) -> chunks[]` | Hybrid retrieval, returns citations with document + page. |
| `sheet.compute` | `(file, operations) -> {result, workbook}` | pandas/openpyxl; shows the formula trail. |
| `doc.ingest` | `(file) -> DocumentRecord` | OCR + layout + VLM pass; see §4.4. |
| `vision.describe` | `(image, question) -> structured` | Routes to the vision model. |
| `deliver.docx` / `.xlsx` / `.pptx` | `(spec) -> file` | See §4.5. |

**Sandbox hardening — Dual Backend Architecture:**

The workbench supports a **dual backend** for code execution:
1. **Production Docker Backend:** When Docker is running, runs in `network_mode: none`, read-only rootfs, non-root user, CPU/memory caps.
2. **Venue Subprocess Backend:** When Docker daemon is inactive or host is constrained (weak laptop), executes in an isolated Python subprocess that:
   - Strips network environment (`HTTP_PROXY`, `HTTPS_PROXY` unset).
   - Injects a socket-override hook (`socket.socket = None` or stubbed to raise `ConnectionError`).
   - Restricts filesystem writes strictly to `./work/out`.
   - Enforces a 60-second execution deadline and memory/process caps.

```yaml
sandbox:
  backend: auto               # "docker" if daemon alive, fallback "subprocess"
  image: etrigan/sandbox:py311
  network_mode: none
  read_only: true
  tmpfs: [/tmp]
  volumes: ["./work:/work:rw"]
  mem_limit: 2g
  cpus: 2.0
  pids_limit: 128
  timeout_seconds: 60
  security_opt: ["no-new-privileges:true"]
```

### 4.4 Document ingest and multimodal (R4)

```
file → type detection
  ├─ born-digital PDF → PyMuPDF text + layout
  ├─ scanned PDF / image → rasterise → OCR (PaddleOCR)
  │                                  → VLM pass (layout, tables, stamps, handwriting)
  │                                  → merge: OCR gives exact characters,
  │                                           VLM gives structure and reading order
  ├─ engineering drawing → VLM with a drawing-specific prompt
  │                        (title block, equipment tags, revision, annotations)
  └─ office file → native parse
        ↓
  DocumentRecord {
      doc_id, source_path, sha256, pages[],
      text_blocks[] {page, bbox, text, confidence},
      entities[] {type, value, page, bbox},   # equipment tag, date, pressure, signatory
      tables[], images[], summary
  }
        ↓
  chunk (structure-aware, ~800 tokens, 15% overlap, never split a table)
        ↓
  embed (BGE-M3) → Postgres/pgvector + tsvector
```

**Make extraction visible.** When the agent reads a scanned inspection report, the UI should show the page image with bounding boxes over the fields it pulled out. That one screen converts "it's an LLM wrapper" into "it actually read the document" for every non-technical judge in the room.

### 4.5 Deliverable generators (R5)

The model never writes a `.docx` directly. It emits a typed spec; a deterministic generator renders it. This is more reliable, keeps organisational templates intact, and is much easier to defend.

```python
class ApprovalNote(BaseModel):
    ref_no: str
    subject: str
    background: str
    findings: list[Finding]        # each carries a citation
    recommendation: str
    financial_implication: str | None
    approver_designation: str
    annexures: list[str]
```

Ship at least these four:

1. **Approval note → .docx** on the organisation's letterhead template, with findings cited back to the source page.
2. **Calculation sheet → .xlsx** with live formulas, not pasted values, plus a "working" sheet showing each step. Engineering judges will check this.
3. **Review deck → .pptx** from a structured outline.
4. **Code → files + test run** in the sandbox, with the run transcript attached.

Every artifact carries a provenance footer: model used, timestamp, source documents with page numbers, audit chain ID.

### 4.6 Knowledge base (R6)

- **Ingest:** point at a folder of manuals, SOPs and correspondence; watch it and re-index on change.
- **Retrieval:** hybrid — dense (pgvector cosine) + lexical (tsvector) → reciprocal-rank fusion → rerank top 30 to top 6.
- **Citations are mandatory.** Every grounded claim carries `document · page · confidence`, and the UI opens the source page on click.
- **Refuse rather than invent.** When the top reranked score is below threshold, say so explicitly. Demonstrate this deliberately in the demo — ask something the KB does not cover and let it decline. Judges remember a system that admits ignorance; it is also the honest answer to the hallucination question before it is asked.
- **Access control:** documents carry a classification label; workspaces carry a clearance. Retrieval filters on it. PSU evaluators care about this more than about your model choice.

### 4.7 Sovereignty monitor and audit chain (R7) — *the winning component*

**Network proof, three layers:**

1. **Enforcement.** All application containers sit on an internal Docker network with no gateway. Nothing in the compose file publishes outbound. The sandbox is `network_mode: none`.
2. **Observation.** A sidecar (`net-monitor`, `network_mode: host`, `NET_ADMIN`) installs an nftables rule logging any outbound packet not destined for the LAN, then tails that log and streams events over WebSocket.
3. **Display.** A persistent header strip, always visible:

   ```
   ● SOVEREIGN   uptime 04:12:33   external attempts 0   blocked 0   models local 4   last egress —
   ```

   If anything ever tries to leave, it turns red and names the process. It will not, and that is the point.

**The stage moment, scripted:** at minute five, ask the agent to run a full multi-step task. While it is mid-execution, **physically unplug the ethernet and turn off wifi.** The task completes. The monitor keeps reading zero. Then say: *"Every cloud assistant in this room just stopped working. This one didn't notice."*

Nothing else you can build for this problem statement lands harder. Rehearse it until it is boring.

**Audit chain:**

```python
class AuditEntry(BaseModel):
    seq: int
    ts: datetime
    session_id: str
    kind: Literal["model_call","tool_call","file_read","file_write","artifact","route"]
    actor: str
    payload_hash: str            # sha256 of arguments
    result_hash: str | None
    prev_hash: str
    entry_hash: str              # sha256(prev_hash + canonical(entry))
```

Append-only, hash-chained, so any edit breaks the chain. Ship `etrigan audit verify` (walks the chain, prints OK/BROKEN) and `etrigan audit export --pdf` (a compliance report an auditor could actually file). Also ship **deterministic replay** — rerun a past session from the audit log with fixed seeds — which is a genuinely rare capability and an excellent answer to "how would we investigate a bad output six months from now?"

### 4.8 Sovereign Fine-Tuning Engine — Soup Integration

**The Problem It Solves:**
General open-weight models (like Llama or Qwen) lack deep familiarity with petrochemical industry conventions — P&ID equipment tag formats (e.g. `FV-101`, `PSV-402`), refinery safety loop standards (IS-2048, OISD-118), and refinery inspection terminology. However, sending confidential refinery documentation or internal schematics to external cloud fine-tuning services (OpenAI, AWS, GCP) is strictly forbidden for security-critical enterprises like ACME.

**How Soup Empowers Etrigan On-Premise:**
We integrate **Soup** (`soup-cli`), a declarative post-training and fine-tuning engine:
1. **Consumer GPU Layer Streaming:** Soup features decoder-layer streaming (`stream_layers: true`), allowing an 8B model to be fine-tuned via QLoRA on a **4 GB laptop GPU** (measured at 119.6 tok/s within a 3.32 GB VRAM peak).
2. **One-Config Declarative Pipeline:** The entire adaptation is controlled via `config/soup.yaml`. No complex multi-node distributed training code or cloud dependencies.
3. **Local Domain Adaptation:** ACME can ingest proprietary incident reports, SOPs, and P&ID annotations into instruction datasets on-premise, fine-tune the model overnight on a local workstation, and immediately hot-register the new adapter in `config/models.yaml` without changing orchestrator code.

```yaml
# config/soup.yaml - ACME Refinery Domain Fine-Tuning Recipe
model:
  base: unsloth/Llama-3.2-3B-Instruct   # or Qwen2.5-3B
  quantization: nf4
  stream_layers: true                  # Enables 4GB VRAM training via layer streaming

training:
  type: sft
  dataset: seed/acme_training_data.jsonl
  lora:
    r: 16
    alpha: 32
    target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
  epochs: 3
  batch_size: 1
  gradient_accumulation_steps: 4
  learning_rate: 2e-4
  output_dir: models/acme-domain-adapter
```

**Judge Presentation Beat:**
> *"How do we guarantee high precision on ACME refinery schematics and internal safety rules without cloud AI? We embed the Sovereign Fine-Tuning Engine via Soup. Using Soup's layer streaming, ACME engineers can fine-tune domain-specialized 8B models locally on a 4 GB workstation GPU without a single byte of confidential refinery data leaving the building."*

---

## 5. Repository layout

```
etrigan/
  docker-compose.yml
  docker-compose.venue.yml         # small-model profile for the stage
  Makefile                         # up, down, seed, bundle, demo, verify
  BUILD_SPEC.md                    # this file
  AGENTS.md                        # conventions for the coding agent
  config/
    models.yaml
    profiles/{venue,server,tiny}.yaml
    tools.yaml
    policy.yaml                    # workspace clearances, tool permissions
  app/                             # FastAPI orchestrator
    main.py  api/  router/  agent/  tools/  ingest/  kb/  deliver/  audit/  models/
  sandbox/                         # sandbox image
  net-monitor/                     # nftables sidecar + WS server
  web/                             # Next.js UI (fonts + icons vendored)
    app/  components/{Chat,PlanPanel,RouterPanel,SourcesPanel,ArtifactsPanel,SovereigntyBar}/
  eval/
    golden/                        # 20 industrial tasks with expected outcomes
    run_eval.py
  bundle/                          # offline installer output
  seed/                            # demo corpus + sample scans
  tests/
```

---

## 6. Build phases

Each phase must end green before the next begins.

### Phase 0 — Skeleton and streaming chat *(≈2 days)*

Compose up: Postgres+pgvector, Ollama, FastAPI, Next.js. One model pulled. Chat with SSE streaming. Sessions persisted. Health endpoint reporting model availability.

**Accept when:** `docker compose up` on a clean machine yields a working streaming chat, and `docker compose down -v && up` reproduces it. Browser devtools shows zero third-party requests.

### Phase 1 — Registry and router *(≈2 days)* → **R1, R2**

`models.yaml` loaded at boot. Three models served. Signal extraction, JSON task classification, candidate filtering, scoring. `RoutingDecision` streamed to the UI before generation. Router panel. `etrigan model add` hot-reload.

**Accept when:** three prompts of different types (write a Python function / summarise a 30-page PDF / describe this photo) route to three different models, each with a readable reason; and a fourth model added live appears and is selectable without a restart.

### Phase 2 — Agent loop and tools *(≈3 days)* → **R3**

Typed `Plan`. Step executor with pre/post audit writes. Tools: `fs.*`, `code.run`, `sheet.compute`. Sandbox image with the hardening in §4.3. Repair-on-failure and replanning. Plan panel rendering live step state.

**Accept when:** "read `inspection_data.csv`, compute mean wall thickness per equipment tag, flag anything below the minimum, and write a summary" completes autonomously — plan visible, code executed in the sandbox, failure injected once and repaired — and the sandbox provably cannot reach the network (`code.run` attempting an HTTP request returns a connection error, on screen).

### Phase 3 — Documents and knowledge base *(≈3 days)* → **R4, R6**

Ingest pipeline for born-digital and scanned PDFs, images and office files. OCR + VLM merge. Structure-aware chunking, BGE-M3 embeddings, hybrid retrieval, reranking. Citations with page anchors. Bounding-box overlay view. Clearance filtering. Below-threshold refusal.

**Accept when:** a scanned inspection report with handwritten annotations is ingested, findings are extracted with bounding boxes shown, `docs.search` returns cited chunks, clicking a citation opens the exact page, and an out-of-corpus question is declined rather than answered.

### Phase 4 — Deliverables *(≈2 days)* → **R5**

The four generators in §4.5, driven by typed specs, with provenance footers.

**Accept when:** the end-to-end task the PS names — *read a scanned inspection report, pull out key findings, draft an approval note as a Word file* — runs start to finish and produces a `.docx` that opens cleanly in Word with correct citations; and a calculation task produces an `.xlsx` with live formulas.

### Phase 5 — Sovereignty and audit *(≈2 days)* → **R7**

Egress-deny network topology. `net-monitor` sidecar. Sovereignty bar. Hash-chained audit. `audit verify`, `audit export --pdf`, deterministic replay.

**Accept when:** the full demo runs with the network physically disconnected; the monitor reads zero throughout; `audit verify` returns OK; manually tampering with one audit row makes it return BROKEN at the right sequence number.

### Phase 6 — Evaluation, bundle, rehearsal *(≈2 days)*

Twenty golden industrial tasks with expected outcomes. `run_eval.py` reporting routing accuracy, task success rate, mean steps, mean latency, sandbox violations (must be zero). Offline bundle (§8). Demo script rehearsed five times on the venue machine.

**Accept when:** `make bundle` produces an installer that works on a machine with networking disabled and no prior Docker images, and the eval prints a table you are willing to put on a slide.

---

## 7. Features that lift it above a competent submission

Build these only after Phase 5 is green.

1. **Golden-set eval with published numbers.** "Routing accuracy 91% over 20 industrial tasks; 17/20 completed autonomously; zero sandbox escapes." Almost no SIH team brings measurements. It changes how the panel listens to everything else you say.
2. **Deterministic replay** from the audit log.
3. **GPU and capacity meter** — tokens processed, GPU-seconds, concurrent sessions, VRAM headroom. A PSU has to plan hardware; show them you know that.
4. **Template pack** — the organisation's own letterhead, note format, approval matrix, as swappable templates. Turns a demo into something installable.
5. **Clearance-aware workspaces** — one login sees a document, another does not, same query. Thirty seconds, and it addresses the first question a PSU officer will ask.
6. **Offline model catalogue** — a local page listing available models, sizes, licences, and what each is good at. Reinforces R2 without a word.

### Deliberately out of scope

Multi-tenant SaaS. Cloud APIs. Mobile apps. Real-time voice agents. Do not let the coding agent build these; keep focus tightly locked on the 7 core requirements and the 8-minute demo.

*(Note on Fine-Tuning: While continuous distributed training runs are not conducted during the 8-minute live demo, the declarative fine-tuning recipe `config/soup.yaml` and the Soup layer-streaming pipeline are shipped as the sovereign domain-adaptation story.)*

---

## 8. Deployment — "where to deploy" is the wrong question here

There is no cloud in this product. Deployment means **an offline installer for a machine that has never had internet**.

**`make bundle` produces:**

```
etrigan-offline-v1.tar
  images.tar          # docker save of every image
  models/             # pre-pulled weights + checksums
  wheels/             # vendored Python wheels (pip --no-index)
  node_modules.tar    # pre-built web assets, fonts and icons vendored
  seed/               # demo corpus
  install.sh          # docker load, compose up, health check, self-test
  VERIFY.md           # checksums + what to expect
```

Target host: Ubuntu 22.04/24.04, NVIDIA driver + container toolkit, 16 GB+ VRAM for the server profile. `install.sh` must complete on a host with networking switched off, then run a self-test that exercises one task per role and prints a pass table.

Say this on stage: *"This installs on a machine that has never been connected to the internet, and we can prove it because that is how we tested it."* It is a one-sentence answer to the only real objection to the whole category.

---

## 9. Demo script — 8 minutes

| Time | Beat |
|---|---|
| 0:00 | "A refinery engineer has a confidential inspection report and a deadline. Policy says it cannot touch a cloud AI. So today the work is done by hand — or the policy quietly gets broken." |
| 0:40 | Show the sovereignty bar: 4 local models, zero external calls. Three seconds, no explanation. |
| 1:10 | Prompt 1 — a coding task. The router panel shows the classification and picks the coder model. Code runs in the sandbox; output appears. |
| 2:10 | Prompt 2 — upload a **scanned** inspection report with handwriting. Router switches to the vision model, visibly. Bounding boxes appear over the extracted findings. |
| 3:20 | Prompt 3 — "draft an approval note from these findings." Plan panel draws five steps. One step fails; the agent repairs it on screen. |
| 4:30 | The `.docx` opens in Word. Citations point back to the report pages. |
| 5:00 | **Unplug the network cable. Turn off wifi.** Run another task. It completes. Monitor still reads zero. *"Every cloud assistant in this room just stopped working."* |
| 6:00 | `etrigan model add` — a new model live, appearing in the router. "Next year's models are a config file." |
| 6:40 | `etrigan audit verify` → OK. Tamper with one row → BROKEN. "This is what an auditor gets." |
| 7:20 | Show `config/soup.yaml` + Fine-Tuning tab. "Domain adaptation on refinery P&IDs runs locally on a 4 GB laptop GPU via Soup layer streaming." |
| 7:45 | "Runs on your GPU, on your premises, on a machine that has never seen the internet. Close." |

**Rules:** never demo against a live model download. Pre-warm every model. Have the tiny profile ready. Screen-record the whole run beforehand — if the laptop dies you narrate over the video and keep your composure.

---

## 10. Judge questions, with answers

**"Isn't this just a wrapper around Ollama?"** — Ollama serves weights. The system is the router, the agent loop, the sandbox, the ingest pipeline, the grounded KB and the audit chain. Swap Ollama for vLLM with one config line; everything above it is unchanged. That substitutability *is* the architecture.

**"Open-weight models are weaker than GPT-class models on refinery P&IDs."** — We solve this in two ways: first, grounding and RAG with strict verification; second, our **Sovereign Fine-Tuning Engine powered by Soup**. Soup allows fine-tuning 8B models on a 4 GB consumer GPU right on-premise using layer streaming. We don't need cloud GPUs to train a domain expert.

**"How do you know it never calls out?"** — Three layers: no gateway on the container network, `network_mode: none` on the sandbox, and an nftables/Windows socket monitor that logs any attempt. And we ran the whole demo with the cable unplugged.

**"What about hallucination on a safety-critical document?"** — Every grounded claim carries a citation to a document and page; below the retrieval threshold it declines instead of guessing; every deliverable carries provenance; and the audit chain lets you replay exactly how any output was produced.

**"Who maintains this when models change?"** — A new model is a YAML block and a weights file. We added one on stage in fifteen seconds.

**"Cost?"** — One GPU server, no per-token billing, no data-egress risk. Quote your GPU-seconds meter.

---

## 11. Conventions for the coding agent (`AGENTS.md` seed)

- Python 3.11, `ruff` + `black`, full type hints, Pydantic v2 for every boundary.
- TypeScript strict. No `any`.
- **No network calls in application code.** No SDK for any hosted AI provider. If a dependency phones home, replace it.
- Every tool: Pydantic schema, docstring, unit test, audit entry.
- Every phase ships with tests that assert its acceptance criteria.
- Secrets via env only; none committed; nothing external to authenticate against anyway.
- Commit per phase with the acceptance evidence in the message.
- When stuck, prefer the simpler mechanism and write down the tradeoff in `docs/decisions.md`.
- Do not add features that are not in this spec. Ask instead.

---

## 12. Risks

| Risk | Mitigation |
|---|---|
| Venue GPU too small | Three profiles; tiny profile loads on CPU. Test on the actual machine early. |
| Open-weight model unreliable at tool calling | Constrained JSON decoding, one tool per step, repair loop, small fixed tool set. |
| OCR poor on Indian scans | PaddleOCR + VLM merge; hand-tune on your own seed corpus, not a public dataset. |
| Agent spirals during the demo | Hard step/time/token caps; scripted prompts; pre-recorded backup. |
| Scope creep | Phase gates. Nothing from §7 before Phase 5 is green. |
| A dependency makes an external call | CI check that runs the test suite with networking disabled. |
