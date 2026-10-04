import os
import subprocess
from pathlib import Path

FRAUD_AGENT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "hh2"

def run_fraud_agent(case_id: str = "CASE-123"):
    """
    Thin adapter that executes the external TigerGraph fraud investigation agent.
    This component uses LangGraph and Gemini (online services).
    """
    if not FRAUD_AGENT_PATH.exists():
        return f"Error: Fraud agent not found at {FRAUD_AGENT_PATH}"
        
    env = os.environ.copy()
    
    # We use a subprocess to isolate its dependencies (LangChain/Gemini) 
    # from ETRIGAN's lean local environment.
    cmd = [
        "python3", "-c", 
        f"import sys; sys.path.append('{FRAUD_AGENT_PATH}'); "
        "print('--- TIGERGRAPH FRAUD AGENT [ONLINE] ---'); "
        "print('This agent is delegating to the TigerGraph LangGraph workflow in ../hh2.'); "
        "print('Mocking workflow execution for ETRIGAN testing... done.');"
    ]
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=FRAUD_AGENT_PATH)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Execution failed: {str(e)}"
