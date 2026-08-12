"""
src/api.py
FastAPI backend — all 7 endpoints.
No business logic lives here — everything delegates to orchestrator, vector_store, etc.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from src.config import cfg
from src.models import (
    HealthResponse, HumanCorrectionRequest,
    ProcessRequest, ProductRecord,
)
from src.orchestrator import load_schema, list_categories, process_document, save_record
from src.retrieval.vector_store import add_human_verified, get_collection_count
from src.agents.excel_agent import confirm_mapping


app = FastAPI(
    title="UniHack Product Intelligence API",
    description="Schema-driven extraction of structured product records from industrial documents.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory record store (keyed by record_id)
# In production this would be SQLite, but JSON files + this dict is sufficient for the hackathon
_records: dict[str, dict] = {}
_audits:  dict[str, list] = {}


def _load_existing_records() -> None:
    """Load any previously saved records from disk into memory on startup."""
    output_dir = Path(cfg.paths.output_dir)
    if not output_dir.exists():
        return
    for record_file in output_dir.glob("*_*.json"):
        if "_audit" in record_file.name:
            continue
        try:
            with open(record_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            _records[data["record_id"]] = data
        except Exception:
            pass


@app.on_event("startup")
def startup():
    _load_existing_records()


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check system status — Ollama connectivity, available models and categories."""
    ollama_ok = False
    models_available: list[str] = []

    try:
        resp = requests.get(f"{cfg.ollama.base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            ollama_ok = True
            tags = resp.json().get("models", [])
            models_available = [m.get("name", "") for m in tags]
    except Exception:
        pass

    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama_reachable=ollama_ok,
        ollama_model=cfg.ollama.text_model,
        models_available=models_available,
        categories_available=list_categories(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /categories
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/categories")
def get_categories():
    """List all available product categories (dynamically read from data/schemas/)."""
    categories = list_categories()
    result = []
    for cat in categories:
        schema = load_schema(cat)
        fields = schema.get("fields", {})
        result.append({
            "category": cat,
            "field_count": len(fields),
            "fields": list(fields.keys()),
            "indexed_products": get_collection_count(cat),
        })
    return {"categories": result}


# ─────────────────────────────────────────────────────────────────────────────
# POST /process  — by file path (for local testing)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/process")
def process_by_path(req: ProcessRequest):
    """
    Process a document by its local file path.
    Returns the full structured product record immediately.
    Use this for local testing and CLI integration.
    """
    if not Path(req.file_path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")

    available = list_categories()
    if req.category not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{req.category}'. Available: {available}",
        )

    try:
        record, audit = process_document(
            source_file=req.file_path,
            category=req.category,
            origin_tag=req.origin_tag,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    record_data = record.model_dump()
    audit_data = [e.model_dump() for e in audit.all_entries()]

    _records[record.record_id] = record_data
    _audits[record.record_id] = audit_data

    record_path, audit_path = save_record(record, audit)

    return {
        "record_id": record.record_id,
        "status": record.status,
        "completeness_pct": record.completeness_pct,
        "filled_fields": record.filled_fields,
        "flagged_fields": record.flagged_fields,
        "total_fields": record.total_fields,
        "record": record_data,
        "saved_to": str(record_path),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /process/upload  — file upload endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/process/upload")
async def process_upload(
    file: UploadFile = File(...),
    category: str = Form(...),
    origin_tag: str = Form("real_manufacturer"),
):
    """
    Process a document uploaded as multipart form data.
    Saves the file temporarily, runs the pipeline, returns the record.
    """
    available = list_categories()
    if category not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{category}'. Available: {available}",
        )

    # Save uploaded file to output dir temporarily
    output_dir = Path(cfg.paths.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = output_dir / f"upload_{file.filename}"

    content = await file.read()
    with open(tmp_path, "wb") as f_out:
        f_out.write(content)

    try:
        record, audit = process_document(
            source_file=str(tmp_path),
            category=category,
            origin_tag=origin_tag,
        )
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

    record_data = record.model_dump()
    audit_data = [e.model_dump() for e in audit.all_entries()]

    _records[record.record_id] = record_data
    _audits[record.record_id] = audit_data

    save_record(record, audit)
    tmp_path.unlink(missing_ok=True)

    return {
        "record_id": record.record_id,
        "status": record.status,
        "completeness_pct": record.completeness_pct,
        "record": record_data,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /record/{record_id}
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/record/{record_id}")
def get_record(record_id: str):
    """Return the full structured product record with all field values and confidence scores."""
    if record_id not in _records:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")
    return _records[record_id]


# ─────────────────────────────────────────────────────────────────────────────
# GET /record/{record_id}/audit
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/record/{record_id}/audit")
def get_audit(record_id: str):
    """Return the full audit trail — every agent decision that produced this record."""
    if record_id not in _audits:
        # Try loading from disk
        output_dir = Path(cfg.paths.output_dir)
        for f in output_dir.glob(f"{record_id}_*_audit.json"):
            with open(f, "r", encoding="utf-8") as fh:
                return {"record_id": record_id, "audit_trail": json.load(fh)}
        raise HTTPException(status_code=404, detail=f"Audit for record '{record_id}' not found")
    return {"record_id": record_id, "audit_trail": _audits[record_id]}


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /record/{record_id}/field/{field_name}  — human correction
# ─────────────────────────────────────────────────────────────────────────────

@app.patch("/record/{record_id}/field/{field_name}")
def human_correction(
    record_id: str,
    field_name: str,
    req: HumanCorrectionRequest,
):
    """
    Apply a human correction to a field.
    The corrected record is:
    1. Updated in memory and on disk
    2. Added to the Chroma vector store as a high-trust reference
       (future similar products will benefit from this correction)
    3. If the field came from Excel, the column mapping is cached
    """
    if record_id not in _records:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")

    record = _records[record_id]

    if field_name not in record.get("fields", {}):
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found in record '{record_id}'",
        )

    # Apply correction
    field = record["fields"][field_name]
    original_value = field.get("value")
    field["corrected_value"] = req.corrected_value
    field["corrected_by"] = req.corrected_by
    from datetime import datetime, timezone
    field["corrected_at"] = datetime.now(timezone.utc).isoformat()
    field["status"] = "human_verified"
    field["method"] = "human_verified"
    field["confidence"] = cfg.confidence.human_verified
    field["flagged"] = False

    # Cache column mapping if this was from Excel
    if field.get("source", "").startswith("Column '"):
        col_match = field["source"].split("'")
        if len(col_match) >= 2:
            confirm_mapping(col_match[1], field_name)

    # Save updated record to disk
    output_dir = Path(cfg.paths.output_dir)
    for record_file in output_dir.glob(f"{record_id}_*.json"):
        if "_audit" not in record_file.name:
            with open(record_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
            break

    # Add to vector store as high-trust reference
    category = record.get("category", "unknown")
    field_text = f"{field_name}: {req.corrected_value}"
    add_human_verified(
        category=category,
        record_id=record_id,
        field_name=field_name,
        corrected_value=req.corrected_value,
        full_field_text=field_text,
    )

    return {
        "record_id": record_id,
        "field": field_name,
        "original_value": original_value,
        "corrected_value": req.corrected_value,
        "status": "human_verified",
        "vector_store_updated": True,
        "message": f"Correction applied. Future similar products will benefit from this correction.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /records  — catalog view
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/records")
def list_records(category: str | None = None):
    """List all processed records with completeness stats."""
    records = list(_records.values())
    if category:
        records = [r for r in records if r.get("category") == category]

    summary = []
    for r in records:
        summary.append({
            "record_id":       r.get("record_id"),
            "category":        r.get("category"),
            "source_file":     Path(r.get("source_file", "")).name,
            "status":          r.get("status"),
            "completeness_pct": r.get("completeness_pct", 0),
            "filled_fields":   r.get("filled_fields", 0),
            "flagged_fields":  r.get("flagged_fields", 0),
            "total_fields":    r.get("total_fields", 0),
            "created_at":      r.get("created_at"),
        })

    return {
        "total": len(summary),
        "records": sorted(summary, key=lambda x: x.get("created_at", ""), reverse=True),
    }
