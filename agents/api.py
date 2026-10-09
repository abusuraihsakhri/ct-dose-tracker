"""
FastAPI REST API Server for Ct Dose Tracker.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Ct Dose Tracker API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "ct-dose-tracker", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=400, detail="Prohibited identifier in request") from None
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=400, detail="Prohibited identifier in request") from None


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}

# Serve the same local-only worksheet when the optional FastAPI backend is running.
# Static JavaScript does not invoke the audit API or transmit dose entries.
from pathlib import Path
from fastapi.responses import FileResponse

_STATIC_ROOT = Path(__file__).resolve().parent.parent

@app.get("/", include_in_schema=False)
def worksheet():
    return FileResponse(_STATIC_ROOT / "index.html", media_type="text/html")

@app.get("/app.mjs", include_in_schema=False)
def worksheet_ui():
    return FileResponse(_STATIC_ROOT / "app.mjs", media_type="text/javascript")

@app.get("/dose.mjs", include_in_schema=False)
def worksheet_calculator():
    return FileResponse(_STATIC_ROOT / "dose.mjs", media_type="text/javascript")
