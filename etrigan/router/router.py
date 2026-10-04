import json
import yaml
from pathlib import Path
from etrigan.diagnostics import check_ram

def load_config():
    with open("config/models.yaml", "r") as f:
        return yaml.safe_load(f)

class MemoryAwareRouter:
    def __init__(self):
        self.config = load_config()
        self.local_models = self.config["providers"]["local"]["models"]
        
    def classify_task(self, prompt: str) -> str:
        """Heuristic classification for speed."""
        prompt_lower = prompt.lower()
        if "python" in prompt_lower or "code" in prompt_lower or "script" in prompt_lower or "calculate" in prompt_lower:
            return "code"
        if "image" in prompt_lower or "scan" in prompt_lower:
            return "vision"
        return "general"

    def route(self, prompt: str):
        task_type = self.classify_task(prompt)
        
        # Determine base model for the task
        base_model = self.local_models.get(task_type, self.local_models["general"])
        
        # Memory check
        total_kb, avail_kb = check_ram()
        avail_gb = (avail_kb / 1024 / 1024) if avail_kb else 4.0 # Default to 4 if unknown
        
        selected_model = base_model
        fallback_used = False
        rationale = f"Task classified as '{task_type}'."
        
        # Fallback logic: if we want a 3B model but RAM is very low (< 2.5GB available), fallback to 1B
        if avail_gb < 2.5 and "3b" in base_model.lower():
            selected_model = "llama3.2:1b"
            fallback_used = True
            rationale += f" Available RAM is critically low ({avail_gb:.1f} GB). Falling back from {base_model} to {selected_model} to prevent out-of-memory errors."
        else:
            rationale += f" Memory is sufficient ({avail_gb:.1f} GB available). Selected {selected_model}."

        # Unloading logic via keep_alive
        keep_alive = "5m" # default
        if avail_gb < 3.5:
            keep_alive = "0"
            rationale += " Memory is tight, setting keep_alive=0 to immediately unload the model after completion. Ensure OLLAMA_MAX_LOADED_MODELS=1 is set in your environment."
            
        return {
            "task_type": task_type,
            "selected_model": selected_model,
            "keep_alive": keep_alive,
            "rationale": rationale,
            "fallback_triggered": fallback_used
        }
