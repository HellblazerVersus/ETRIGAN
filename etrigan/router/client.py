import os
from typing import Dict, Any, Tuple
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "models.yaml"

def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {
            "mode": "api",
            "providers": {
                "api": {
                    "base_url": os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
                    "api_key_env": "LLM_API_KEY",
                    "models": {
                        "classifier": "llama-3.1-8b-instant",
                        "general": "llama-3.3-70b-versatile",
                        "code": "qwen-2.5-coder-32b",
                        "vision": "llama-3.2-11b-vision-preview"
                    }
                }
            }
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

_ACTIVE_MODEL_OVERRIDE = None

def set_active_model_override(model_name: str | None):
    global _ACTIVE_MODEL_OVERRIDE
    if not model_name or model_name.lower() in ["auto", "none"]:
        _ACTIVE_MODEL_OVERRIDE = None
    else:
        _ACTIVE_MODEL_OVERRIDE = model_name

def get_active_model_override() -> str | None:
    return _ACTIVE_MODEL_OVERRIDE

def get_client_config(role: str = "general") -> Tuple[str, str, str]:
    """
    Returns (base_url, api_key, model_name) based on active override or mode (api vs local).
    Both API and Ollama use the identical OpenAI-compatible protocol.
    """
    cfg = load_config()
    mode = os.getenv("MODE", cfg.get("mode", "api")).lower()
    provider = cfg.get("providers", {}).get(mode, {})
    
    base_url = provider.get("base_url", "http://localhost:11434/v1")
    api_key_env = provider.get("api_key_env", "")
    api_key = os.getenv(api_key_env, "ollama-local") if api_key_env else "ollama-local"
    
    if _ACTIVE_MODEL_OVERRIDE:
        return base_url, api_key, _ACTIVE_MODEL_OVERRIDE
        
    models = provider.get("models", {})
    model_name = models.get(role, models.get("general", "llama3.2:1b"))
    
    return base_url, api_key, model_name
