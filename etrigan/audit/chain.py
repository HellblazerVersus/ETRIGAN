import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, Any, Tuple
from pathlib import Path
from etrigan.kb.store import get_db_connection

GENESIS_HASH = "0" * 64

def log_audit_entry(
    session_id: str,
    kind: str,
    actor: str,
    payload: Dict[str, Any],
    result: Any = None
) -> Dict[str, Any]:
    """
    Appends an immutable, SHA-256 hash-chained entry to the audit log in SQLite.
    Every entry is cryptographically linked to the previous entry hash.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get previous entry hash
    cursor.execute("SELECT seq, entry_hash FROM audit_chain ORDER BY seq DESC LIMIT 1")
    last_row = cursor.fetchone()
    
    if last_row:
        seq = last_row[0] + 1
        prev_hash = last_row[1]
    else:
        seq = 1
        prev_hash = GENESIS_HASH
        
    ts = datetime.now().isoformat()
    payload_str = str(sorted(payload.items())) if isinstance(payload, dict) else str(payload)
    payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    
    result_str = str(result) if result is not None else ""
    result_hash = hashlib.sha256(result_str.encode("utf-8")).hexdigest()
    
    # Compute cryptographically linked entry hash
    canonical = f"{seq}|{ts}|{session_id}|{kind}|{actor}|{payload_hash}|{result_hash}|{prev_hash}"
    entry_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    
    cursor.execute("""
    INSERT INTO audit_chain (seq, ts, session_id, kind, actor, payload_hash, result_hash, prev_hash, entry_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (seq, ts, session_id, kind, actor, payload_hash, result_hash, prev_hash, entry_hash))
    
    conn.commit()
    conn.close()
    
    return {
        "seq": seq,
        "entry_hash": entry_hash,
        "prev_hash": prev_hash,
        "ts": ts
    }

def verify_audit_chain() -> Tuple[bool, str]:
    """
    Walks the entire audit log and verifies every cryptographic link.
    Returns (True, 'OK: N entries verified') or (False, 'TAMPERED at sequence N').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT seq, ts, session_id, kind, actor, payload_hash, result_hash, prev_hash, entry_hash FROM audit_chain ORDER BY seq ASC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return True, "Audit log is empty (0 entries)."
        
    expected_prev = GENESIS_HASH
    for row in rows:
        seq, ts, session_id, kind, actor, payload_hash, result_hash, prev_hash, entry_hash = row
        
        # 1. Check previous hash linkage
        if prev_hash != expected_prev:
            return False, f"TAMPERED at sequence #{seq}: prev_hash mismatch. Expected {expected_prev[:12]}..., got {prev_hash[:12]}..."
            
        # 2. Recompute entry hash
        canonical = f"{seq}|{ts}|{session_id}|{kind}|{actor}|{payload_hash}|{result_hash}|{prev_hash}"
        recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        
        if recomputed != entry_hash:
            return False, f"TAMPERED at sequence #{seq}: entry payload modified! Hash mismatch."
            
        expected_prev = entry_hash
        
    return True, f"OK: Verified {len(rows)} sequential audit records with zero tamper."

def get_recent_audit_entries(limit: int = 10) -> list:
    """Returns the most recent audit entries for frontend inspection."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT seq, ts, session_id, kind, actor, payload_hash, result_hash, prev_hash, entry_hash FROM audit_chain ORDER BY seq DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    entries = []
    for r in rows:
        entries.append({
            "seq": r[0],
            "ts": r[1],
            "session_id": r[2],
            "kind": r[3],
            "actor": r[4],
            "payload_hash": r[5],
            "result_hash": r[6],
            "prev_hash": r[7],
            "entry_hash": r[8]
        })
    return entries
