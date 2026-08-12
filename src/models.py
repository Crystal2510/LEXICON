"""
src/models.py
All Pydantic data models for the pipeline.
Every field in the output carries: value, source, method, confidence, audit trail.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# Audit Trail
# ─────────────────────────────────────────────────────────────────────────────

class AuditEntry(BaseModel):
    """One decision step logged by any agent."""
    step: int
    field: str
    agent: str           # document_agent | excel_agent | rag_enrichment | validation | orchestrator
    action: str          # extract_attempt | validate | rag_fallback | flag_for_review | human_correction
    input_summary: str   # truncated description of what was fed in
    output_summary: str  # what came out
    result: str          # success | failed | flagged | skipped
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────────────────────────────────────
# Extraction result from a single agent call (internal use)
# ─────────────────────────────────────────────────────────────────────────────

class ExtractionResult(BaseModel):
    """Raw result from one agent extraction attempt."""
    value: Any = None                    # extracted value (None = not found)
    source_span: str = ""               # exact quoted text where value was found
    unit_found: str | None = None       # unit as it appeared in the document
    page_number: int | None = None      # page number (PDF only)
    column_name: str | None = None      # original column header (Excel only)
    agent: str = ""
    raw_llm_response: str = ""          # full LLM output for debugging


# ─────────────────────────────────────────────────────────────────────────────
# Validation result
# ─────────────────────────────────────────────────────────────────────────────

class ValidationResult(BaseModel):
    passed: bool
    reason: str          # e.g. "value 6.0 is within [0.5, 400]" or "value 9999 exceeds max 400"
    converted_value: Any = None   # if unit was converted, the converted value


# ─────────────────────────────────────────────────────────────────────────────
# Final per-field record (what appears in the output JSON)
# ─────────────────────────────────────────────────────────────────────────────

class FieldRecord(BaseModel):
    value: Any = None
    unit: str | None = None
    source: str = ""             # "SKF-Rolling-Bearings.pdf p.23" or "catalog.xlsx col B:bore"
    method: str = "not_found"   # direct_text | direct_excel | direct_image | rag_inferred | human_verified | not_found
    confidence: float = 0.0
    in_range: bool = True
    flagged: bool = False        # True = needs human review
    status: str = "ok"          # ok | needs_review | not_found | human_verified
    sources_agreed: bool = False # True if same value found in multiple independent sources
    audit_entries: list[AuditEntry] = Field(default_factory=list)

    # Human correction fields (populated when a reviewer corrects a value)
    corrected_value: Any = None
    corrected_by: str | None = None
    corrected_at: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Ingested document (output of ingestion stage)
# ─────────────────────────────────────────────────────────────────────────────

class IngestedDocument(BaseModel):
    doc_id: str
    doc_type: str           # pdf | excel | image
    origin_tag: str         # real_manufacturer | real_directindustry | team_assembled | synthetic_adversarial
    source_file: str
    text: str = ""
    pages: list[dict] = Field(default_factory=list)   # [{page_no, text}]
    tables: list[dict] = Field(default_factory=list)  # [{page_no, rows}]
    raw_rows: list[dict] = Field(default_factory=list) # Excel rows
    raw_headers: list[str] = Field(default_factory=list) # Excel original headers
    image_path: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Full product record
# ─────────────────────────────────────────────────────────────────────────────

class ProductRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: str
    origin_tag: str
    source_file: str
    fields: dict[str, FieldRecord] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "complete"          # complete | partial | needs_review
    total_fields: int = 0
    filled_fields: int = 0
    flagged_fields: int = 0
    completeness_pct: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# API request/response models
# ─────────────────────────────────────────────────────────────────────────────

class ProcessRequest(BaseModel):
    file_path: str
    category: str
    origin_tag: str = "real_manufacturer"


class HumanCorrectionRequest(BaseModel):
    corrected_value: Any
    corrected_by: str = "reviewer"


class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool
    ollama_model: str
    models_available: list[str]
    categories_available: list[str]
