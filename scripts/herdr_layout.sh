#!/bin/bash
# Opens one workspace with panes for ollama, orchestrator (CLI), agent run, resource stats, and eval.

echo "Setting up ETRIGAN Herdr workspace..."

# 1. Main pane is already the CLI (agent run). Let's get its ID.
PANE_MAIN=$HERDR_PANE_ID
if [ -z "$PANE_MAIN" ]; then
  echo "Not running inside herdr. Please run this inside a herdr session."
  exit 1
fi

# 2. Split right for Ollama
RES_OLLAMA=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus --json 2>/dev/null)
PANE_OLLAMA=$(echo "$RES_OLLAMA" | grep -oP '"pane_id":"\K[^"]+')
if [ -n "$PANE_OLLAMA" ]; then
    herdr pane run "$PANE_OLLAMA" "./bin/ollama serve"
fi

# 3. Split down from main for resource stats (htop or watch)
RES_STATS=$(herdr pane split --current --direction down --cwd "$PWD" --no-focus --json 2>/dev/null)
PANE_STATS=$(echo "$RES_STATS" | grep -oP '"pane_id":"\K[^"]+')
if [ -n "$PANE_STATS" ]; then
    herdr pane run "$PANE_STATS" "watch -n 2 'free -m; echo; nvidia-smi'"
fi

# 4. Split down from ollama for eval/tests
RES_EVAL=$(herdr pane split --pane "$PANE_OLLAMA" --direction down --cwd "$PWD" --no-focus --json 2>/dev/null)
PANE_EVAL=$(echo "$RES_EVAL" | grep -oP '"pane_id":"\K[^"]+')
if [ -n "$PANE_EVAL" ]; then
    herdr pane run "$PANE_EVAL" "source .venv/bin/activate && python3 etrigan_cli.py shell"
fi

echo "Workspace layout complete."
