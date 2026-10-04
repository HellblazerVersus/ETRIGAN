import socket
import json
import os
import uuid

def report_state(state: str):
    """
    Sends agent state (idle/working/blocked) to Herdr's socket API.
    Fails silently if the socket does not exist or connection fails.
    """
    if state not in ["idle", "working", "blocked"]:
        return

    sock_path = os.environ.get("ETRIGAN_HERDR_SOCKET", os.path.expanduser("~/.config/herdr/herdr.sock"))
    
    if not os.path.exists(sock_path):
        return

    pane_id = os.environ.get("HERDR_PANE_ID", "")
    
    # Herdr API Protocol 22 Request
    payload = {
        "jsonrpc": "2.0",
        "method": "pane_agent_status_changed", # or similar state update
        "params": {
            "agent_status": state,
            "pane_id": pane_id
        },
        "id": str(uuid.uuid4())
    }

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(1.0)
        client.connect(sock_path)
        client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        client.close()
    except Exception:
        pass # Fail silently per spec
