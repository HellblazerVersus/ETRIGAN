import time
import json
import os
import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Basic mocked or real HTTP client for Ollama
# In a real app we'd use httpx or requests, but we can rely on standard library or requests if available.
import urllib.request
import urllib.error

OLLAMA_URL = "http://127.0.0.1:11434"

PROMPTS = {
    "short": "Hello, how are you?",
    "summary": "Summarize the following text in 5 sentences: " + "ETRIGAN is a sovereign AI workbench... " * 50,
    "code": "Write a Python script to calculate the Fibonacci sequence up to 100."
}

def get_ollama_version() -> str:
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/version")
        with urllib.request.urlopen(req, timeout=2) as response:
            return json.loads(response.read().decode())["version"]
    except Exception:
        return "unknown"

def get_loaded_models() -> List[Dict]:
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/ps")
        with urllib.request.urlopen(req, timeout=2) as response:
            return json.loads(response.read().decode()).get("models", [])
    except Exception:
        return []

def run_prompt(model: str, prompt: str) -> Dict[str, Any]:
    """Runs a single prompt and returns the Ollama metrics."""
    data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            return {
                "eval_count": res.get("eval_count", 0),
                "eval_duration": res.get("eval_duration", 1), # nanoseconds
                "prompt_eval_duration": res.get("prompt_eval_duration", 0),
            }
    except Exception as e:
        return {"error": str(e)}

def parse_benchmark_log(metrics: Dict[str, Any]) -> Dict[str, float]:
    """Parses raw Ollama nanosecond metrics into human readable stats."""
    if "error" in metrics:
        return {"error": metrics["error"]}
        
    eval_count = metrics.get("eval_count", 0)
    eval_duration_ns = metrics.get("eval_duration", 1)
    prompt_eval_ns = metrics.get("prompt_eval_duration", 0)
    
    # 1 second = 1,000,000,000 ns
    tokens_per_sec = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns else 0
    ttft_ms = prompt_eval_ns / 1e6
    
    return {
        "tokens_per_sec": round(tokens_per_sec, 2),
        "ttft_ms": round(ttft_ms, 2)
    }

def benchmark_model(model: str) -> Dict[str, Any]:
    """Runs warmup and 3 timed runs for each prompt type."""
    results = {}
    for p_name, p_text in PROMPTS.items():
        # Warmup
        run_prompt(model, p_text)
        
        runs = []
        for _ in range(3):
            raw = run_prompt(model, p_text)
            parsed = parse_benchmark_log(raw)
            if "error" not in parsed:
                runs.append(parsed)
                
        if runs:
            avg_tps = sum(r["tokens_per_sec"] for r in runs) / len(runs)
            avg_ttft = sum(r["ttft_ms"] for r in runs) / len(runs)
            results[p_name] = {"avg_tokens_per_sec": round(avg_tps, 2), "avg_ttft_ms": round(avg_ttft, 2)}
        else:
            results[p_name] = {"error": "Failed to generate"}
            
    # Polling /api/ps to see memory split
    ps_data = get_loaded_models()
    vram_share = 0
    for m in ps_data:
        if m.get("name") == model:
            size = m.get("size", 1)
            size_vram = m.get("size_vram", 0)
            vram_share = round((size_vram / size) * 100, 1)
            break
            
    return {
        "model": model,
        "runs": results,
        "gpu_vram_share_percent": vram_share
    }

def save_benchmark(model: str, result: Dict[str, Any], hw_label: str):
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = Path(f"results/bench_{model.replace(':', '_')}_{date_str}.json")
    
    payload = {
        "timestamp": datetime.datetime.now().isoformat(),
        "hardware_label": hw_label,
        "ollama_version": get_ollama_version(),
        "benchmark": result
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    return filepath
