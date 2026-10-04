<div align="center">
  <img src="assets/logo.svg" alt="ETRIGAN Logo" width="200"/>
  <h1>ETRIGAN</h1>
  <p><b>Sovereign On-Premise Agentic AI Workbench</b></p>
  <p>
    [![CI](https://github.com/HellblazerVersus/ETRIGAN/actions/workflows/ci.yml/badge.svg)](https://github.com/HellblazerVersus/ETRIGAN/actions/workflows/ci.yml)
  </p>
</div>

---

## 📖 Overview

**ETRIGAN** is an engineering-focused AI orchestrator built to run intelligent agentic workflows on standard laptops. Designed specifically to operate under strict hardware constraints (e.g., Intel CPUs, NVIDIA RTX 2050 with 4GB VRAM, and < 4GB available WSL RAM), ETRIGAN provides a robust, offline-first terminal workspace.

## ✨ Core Engineering Features

### 🧠 Memory-Aware Dynamic Routing
The router intercepts requests, dynamically falls back to a lighter quantization (e.g., 1B instead of 3B parameters), and injects `keep_alive=0` payloads to Ollama to instantly purge the model from memory post-inference, preventing OOM crashes.

### ⚡ Hardware Profiling & Benchmarking
Don't guess performance—measure it. Here is a real run from the primary hardware target (8C WSL, RTX 2050 4GB):

```text
Date: 2026-10-04 | Hardware: 8C_WSL / RTX 2050 (4GB) | Ollama: v0.34.3

Benchmarking model: qwen2.5:1.5b
GPU VRAM Share: 100.0%
 - Short   : 85.25 tokens/s, TTFT: 12.7 ms
 - Summary : 83.68 tokens/s, TTFT: 12.72 ms
 - Code    : 81.06 tokens/s, TTFT: 19.49 ms
```

### 🛡️ Zero-Egress & Auditing
- **100% Offline**: ETRIGAN communicates strictly via localhost endpoints. *(Note: The `/fraud` workflow uses Gemini and is an explicit online exception).*
- **SQLite Hybrid RAG**: Uses a pluggable local SQLite FTS5 engine paired with in-memory NumPy cosine similarity for fast, offline document retrieval.
- **Tamper-Evident Audit Logs**: Every agent action and tool execution is recorded in an append-only hash chain.

## 💻 The CLI Experience

![CLI Screenshot](assets/screenshot.png)
*(CLI interface showing hardware diagnostics and workflows)*

| Command | Description |
| :--- | :--- |
| `/doctor` | Run system diagnostics (GPU, WSL RAM, Disk, Dependencies). |
| `/bench` | Benchmark local models on your exact hardware setup. |
| `/fit` | Get VRAM/RAM-aware model quantization recommendations. |
| `/load` | Interactively browse and inject external project files. |
| `/herdr` | Automatically split your terminal into an advanced monitoring workspace. |
| `/fraud` | Run the external **TigerGraph** fraud investigation adapter *(Online)*. |
| `/soup` | View the `layer_streaming` configuration for local fine-tuning. |

## 📐 Architecture
![Architecture Diagram](assets/architecture.png)

## 📊 Evaluation
Hybrid retrieval performance on a small, hand-authored synthetic Hindi/English query set:
- **Recall@3**: 1.00
- **MRR**: 1.00

## 🚧 Limitations
- **Hardware Tested**: Extensively tested on a single machine profile (RTX 2050 4GB, ~3.8GB WSL RAM).
- **Features Planned**: Soup fine-tuning currently exists as a configuration only; actual training runs are pending.
- **Dependencies**: Relies exclusively on `ollama` for inference.

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/HellblazerVersus/ETRIGAN.git
cd ETRIGAN

# Create environment and install as a package
uv venv --python 3.12 .venv
source .venv/bin/activate
pip install -e .
```

### 2. Launching the Workbench
```bash
# Start the Ollama backend in a separate pane/tab
ollama serve

# Launch the ETRIGAN interactive shell
etrigan
```

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
