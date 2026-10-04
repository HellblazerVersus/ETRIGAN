import os
from pathlib import Path
from typing import List, Dict, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent / "work"
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

def _resolve_safe_path(rel_path: str) -> Path:
    """
    Resolves relative path within WORKSPACE_ROOT. Rejects path traversal attempts.
    """
    clean_path = (WORKSPACE_ROOT / rel_path.lstrip("/")).resolve()
    if not str(clean_path).startswith(str(WORKSPACE_ROOT)):
        raise PermissionError(f"Access Denied: Path traversal detected for '{rel_path}'")
    return clean_path

def fs_list(subpath: str = "") -> List[Dict[str, Any]]:
    """
    Lists files and directories under workspace root.
    """
    target = _resolve_safe_path(subpath)
    if not target.exists():
        return []
    
    entries = []
    for item in target.iterdir():
        entries.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "size_bytes": item.stat().st_size if item.is_file() else 0
        })
    return entries

def fs_read(rel_path: str, max_chars: int = 15000) -> str:
    """
    Reads text content of a workspace file up to max_chars.
    """
    target = _resolve_safe_path(rel_path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"File not found: {rel_path}")
        
    with open(target, "r", encoding="utf-8", errors="replace") as f:
        content = f.read(max_chars)
    return content

def fs_write(rel_path: str, content: str) -> Dict[str, Any]:
    """
    Writes text content to a file strictly within WORKSPACE_ROOT/out or subdirectories.
    """
    target = _resolve_safe_path(rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
        
    return {
        "status": "success",
        "file": str(target.relative_to(WORKSPACE_ROOT)),
        "bytes_written": len(content.encode("utf-8"))
    }
