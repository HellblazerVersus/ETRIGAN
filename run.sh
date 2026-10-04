#!/usr/bin/env bash
# run.sh - Launch ETRIGAN Prototype Orchestrator & UI

set -e

echo "=========================================================="
echo "    ETRIGAN — Sovereign On-Premise AI Workbench (DEMO-PROJECT)"
echo "=========================================================="

cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "[!] .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "[!] Please configure your LLM_API_KEY in .env if using mode: api"
fi

export OLLAMA_MODELS=/mnt/d/projects/SIH/models

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "[*] Starting local Ollama server (models stored on D: drive)..."
    /mnt/d/projects/SIH/bin/ollama serve > /mnt/d/projects/SIH/data/ollama.log 2>&1 &
    sleep 3
fi

# Activate virtual environment if present
if [ -d ".venv" ]; then
    echo "[*] Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

echo "[*] ETRIGAN Sovereign Orchestrator ready on http://localhost:8000"
echo "[*] Open web/index.html in your browser to interact."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
