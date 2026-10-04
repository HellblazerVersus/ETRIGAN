import os
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any

import httpx
from etrigan.router.router import classify_and_route, stream_chat_completion
from etrigan.deliver.generators import generate_approval_note, generate_calculation_sheet, generate_technical_presentation, DELIVERABLES_DIR
from etrigan.router.client import load_config, get_active_model_override, set_active_model_override
from etrigan.agent.loop import run_agent_loop
from etrigan.audit.chain import verify_audit_chain, log_audit_entry
from etrigan.kb.store import hybrid_search, get_db_connection, ingest_pdf_document

app = FastAPI(
    title="ETRIGAN Sovereign AI Workbench",
    description="On-Premise Industrial AI Workbench (DEMO-PROJECT)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@app.get("/api/health")
async def health_check():
    cfg = load_config()
    mode = os.getenv("MODE", cfg.get("mode", "api"))
    return {
        "status": "healthy",
        "mode": mode,
        "sovereign_egress": 0,
        "hardware_profile": "venue_integrated_graphics" if mode == "local" else "cloud_dev_api"
    }

class ModelSelectRequest(BaseModel):
    model: str

@app.get("/api/models/active")
async def get_active_model_endpoint():
    override = get_active_model_override()
    available = ["llama3.2:1b", "qwen2.5:1.5b"]
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                available = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return {
        "active": override or "auto",
        "mode": "manual" if override else "auto_router",
        "available": available
    }

@app.post("/api/models/select")
async def select_model_endpoint(req: ModelSelectRequest):
    set_active_model_override(req.model)
    return {
        "status": "success",
        "active": get_active_model_override() or "auto",
        "message": f"Active model set to: {req.model}"
    }

@app.post("/api/route")
async def route_task(req: ChatRequest):
    decision = await classify_and_route(req.message)
    return decision

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    # 1. Route task
    decision = await classify_and_route(req.message)
    role = decision["role"]
    
    # 2. Build conversation context
    system_prompt = (
        "You are ETRIGAN, an on-premise industrial AI assistant for Mangalore Refinery and Petrochemicals Limited (ACME). "
        "You operate in a sovereign environment. Provide technical, grounded, safety-compliant answers. "
        "Cite standards like API 570, OISD, and ASME where applicable."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(req.history[-6:])  # Include recent context
    messages.append({"role": "user", "content": req.message})
    
    async def sse_event_stream():
        # First send the routing decision event
        yield f"event: route\ndata: {json.dumps(decision)}\n\n"
        
        # Stream the tokens
        async for chunk in stream_chat_completion(messages, role=role):
            yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
            
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
        
    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")

class AgentRunRequest(BaseModel):
    goal: str
    session_id: str = None

@app.post("/api/agent/run")
async def agent_run_endpoint(req: AgentRunRequest):
    """
    Executes the multi-step agent loop with live plan rendering, tool calling, and repair.
    Streams SSE events for UI PlanPanel.
    """
    async def sse_agent_stream():
        async for evt in run_agent_loop(req.goal, req.session_id):
            yield f"event: {evt.get('event', 'message')}\ndata: {json.dumps(evt)}\n\n"
            
    return StreamingResponse(sse_agent_stream(), media_type="text/event-stream")

@app.post("/api/deliver/docx")
async def create_docx(
    subject: str = Form("Urgent Replacement of Overhead Piping Spool 12-CDU-0104"),
    findings: str = Form("1. Ultrasonic thickness gauged at 3.1 mm (Retirement T_min: 3.42 mm).\n2. Localized pitting corrosion observed near elbow E-04."),
    recommendation: str = Form("Approve procurement and replacement during October maintenance window.")
):
    findings_list = [f.strip() for f in findings.split("\n") if f.strip()]
    filename = generate_approval_note(subject, findings_list, recommendation)
    return {"filename": filename, "download_url": f"/api/download/{filename}"}

@app.post("/api/deliver/xlsx")
async def create_xlsx(equipment_tag: str = Form("12-CDU-0104")):
    sample_readings = [
        {"point_id": "CML-01", "location": "Upstream Flange", "design": 7.1, "actual": 6.8},
        {"point_id": "CML-02", "location": "Straight Run", "design": 7.1, "actual": 5.4},
        {"point_id": "CML-03", "location": "Elbow Intrados", "design": 7.1, "actual": 4.1},
        {"point_id": "CML-04", "location": "Elbow Extrados", "design": 7.1, "actual": 3.1},
        {"point_id": "CML-05", "location": "Downstream Flange", "design": 7.1, "actual": 6.5},
    ]
    filename = generate_calculation_sheet(equipment_tag, sample_readings, min_thickness=3.42)
    return {"filename": filename, "download_url": f"/api/download/{filename}"}

@app.api_route("/api/download/{filename}", methods=["GET", "HEAD"])
async def download_file(filename: str):
    file_path = DELIVERABLES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Deliverable not found")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/api/deliverables")
async def list_deliverables():
    files = []
    for f in DELIVERABLES_DIR.glob("*.*"):
        if f.suffix in [".docx", ".xlsx", ".pptx", ".pdf"]:
            files.append({
                "name": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "download_url": f"/api/download/{f.name}"
            })
    return {"files": sorted(files, key=lambda x: x["name"], reverse=True)}
    
@app.post("/api/deliver/pptx")
async def create_pptx(
    equipment_tag: str = Form("12-CDU-0104"),
    subject: str = Form("Turnaround Replacement Briefing for Corroded Spool 12-CDU-0104"),
    recommendation: str = Form("Procure replacement ASTM A106 Gr. B spool for scheduled turnaround window.")
):
    findings = [
        f"Equipment Tag {equipment_tag}: Schedule 40 Carbon Steel CDU-II crude overhead line.",
        "Ultrasonic Gauging: Minimum observed thickness 3.12 mm (Elbow extrados CML-04).",
        "Calculated Retirement Limit (T_min): 3.42 mm under 14.8 barg design pressure (ASME B31.3).",
        "Deficit: -0.30 mm below minimum structural threshold.",
        "Corrosion Mechanism: Acid dew-point attack & NH4Cl deposition.",
        "Standard Compliance: Mandatory replacement per ACME SOP-CDU-042 (Rev 04)."
    ]
    filename = generate_technical_presentation(equipment_tag, subject, findings, recommendation)
    return {"filename": filename, "download_url": f"/api/download/{filename}"}

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "work" / "in"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/api/ingest/upload")
async def upload_document_endpoint(file: UploadFile = File(...)):
    """
    Accepts PDF/drawing uploads, extracts text, indexes into SQLite FTS5 RAG,
    and logs SHA-256 hash into the audit chain.
    """
    dest = UPLOAD_DIR / file.filename
    content = await file.read()
    dest.write_bytes(content)
    
    # Ingest if PDF
    if file.filename.lower().endswith(".pdf"):
        res = ingest_pdf_document(str(dest), title=dest.stem.replace("_", " ").title())
        chunks = res.get("chunks_inserted", 0)
    else:
        chunks = 1
        
    # Log in SHA-256 audit chain
    log_audit_entry(
        session_id="upload_session",
        kind="doc_upload",
        actor="plant_engineer",
        payload={"filename": file.filename, "size_bytes": len(content)},
        result={"status": "ingested", "chunks": chunks}
    )
    
    return {
        "filename": file.filename,
        "size_bytes": len(content),
        "chunks_indexed": chunks,
        "message": f"Successfully ingested {file.filename} into grounded RAG knowledge base."
    }

@app.get("/api/audit/verify")
async def audit_verify_endpoint():
    """
    Cryptographically verifies the append-only SHA-256 audit chain.
    """
    valid, message = verify_audit_chain()
    return {"valid": valid, "message": message}

@app.get("/api/audit/log")
async def audit_log_endpoint(limit: int = 20):
    """
    Returns recent entries from the hash-chained audit log.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT seq, ts, session_id, kind, actor, payload_hash, prev_hash, entry_hash 
    FROM audit_chain ORDER BY seq DESC LIMIT ?
    """, (limit,))
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
            "payload_hash": r[5][:10] + "...",
            "prev_hash": r[6][:10] + "...",
            "entry_hash": r[7][:10] + "..."
        })
    return {"entries": entries}

@app.get("/api/kb/search")
async def kb_search_endpoint(query: str, top_k: int = 4):
    """
    Hybrid search across ACME internal documents, returning citations.
    """
    results = hybrid_search(query, top_k=top_k)
    return {"query": query, "results": results}

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="static_web")

