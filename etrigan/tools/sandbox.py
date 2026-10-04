import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent / "work"
OUT_DIR = WORKSPACE_ROOT / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Python prelude script injected before user code to enforce zero network egress
NETWORK_JAIL_PRELUDE = """
import socket

class BlockedNetworkError(ConnectionError):
    pass

_orig_socket = socket.socket

class _JailedSocket(_orig_socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def connect(self, *args, **kwargs):
        raise BlockedNetworkError("Sovereign Sandbox: External network access strictly prohibited by policy (DEMO-PROJECT).")
        
    def connect_ex(self, *args, **kwargs):
        raise BlockedNetworkError("Sovereign Sandbox: External network access strictly prohibited by policy (DEMO-PROJECT).")
        
    def sendto(self, *args, **kwargs):
        raise BlockedNetworkError("Sovereign Sandbox: Outbound packets strictly prohibited.")

def _block_conn(*args, **kwargs):
    raise BlockedNetworkError("Sovereign Sandbox: External connection strictly prohibited by policy (DEMO-PROJECT).")

socket.socket = _JailedSocket
socket.create_connection = _block_conn
socket.getaddrinfo = _block_conn
"""

def execute_sandboxed_code(
    code: str, 
    timeout_seconds: int = 45
) -> Dict[str, Any]:
    """
    Executes Python code in an isolated subprocess sandbox.
    Enforces zero-network policy, execution deadline, and captures outputs.
    """
    # Create wrapped code with network jail prelude
    full_script = f"{NETWORK_JAIL_PRELUDE}\n\n# User Script:\n{code}"
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=str(WORKSPACE_ROOT)) as tmp:
        tmp.write(full_script)
        script_path = tmp.name

    env = os.environ.copy()
    # Strip any proxy variables
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY"]:
        env.pop(key, None)
    
    # Point python to our venv
    venv_python = Path(sys.executable)

    try:
        proc = subprocess.run(
            [str(venv_python), script_path],
            cwd=str(WORKSPACE_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "success": proc.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_seconds} seconds.",
            "success": False
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Sandbox execution failure: {str(e)}",
            "success": False
        }
    finally:
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except OSError:
                pass
