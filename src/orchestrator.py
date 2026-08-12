"""
src/orchestrator.py
The core pipeline loop.

For every required field in the category schema it:
  1. Tries direct extraction from the ingested document (PDF or Excel)
  2. Validates the value against schema min/max/enum
  3. Falls back to RAG-grounded extraction if direct fails
  4. Flags for human review if both fail

ZERO hardcoded field names, categories, or values.
Everything is driven by the schema JSON file read at runtime.
The model name, retry caps, and confidence thresholds all come from config.yaml.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from src.config import cfg
from src.models import (
    AuditEntry, ExtractionResult, FieldRecord,
    IngestedDocument, ProductRecord,
)
from src.audit import AuditLogger
from src.validation.schema_validator import validate_field
from src.ingestion.pdf_reader import get_chunks_for_field
from src.agents import document_agent, excel_agent
from src.retrieval import vector_store


# ─────────────────────────────────────────────────────────────────────────────
# Schema loading
# ─────────────────────────────────────────────────────────────────────────────

def load_schema(category: str) -> dict:
    """
    Load the JSON schema for a category.
    Raises FileNotFoundError if the schema doesn't exist.
    """
    schemas_dir = Path(cfg.paths.schemas_dir)
    path = schemas_dir / f"{category}.json"
    if not path.exists():
        available = [p.stem for p in schemas_dir.glob("*.json")]
        raise FileNotFoundError(
            f"No schema found for category '{category}'. "
            f"Available: {available}. "
            f"Add a JSON schema to {schemas_dir}/ to support this category."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_categories() -> list[str]:
    """Return all available category names (schema stems)."""
    schemas_dir = Path(cfg.paths.schemas_dir)
    return [p.stem for p in sorted(schemas_dir.glob("*.json"))]


# ─────────────────────────────────────────────────────────────────────────────
# Single-field processing
# ─────────────────────────────────────────────────────────────────────────────

def _process_field(
    field_name: str,
    field_def: dict,
    doc: IngestedDocument,
    category: str,
    audit: AuditLogger,
) -> FieldRecord:
    """
    Run the full extraction → validation → RAG fallback loop for one field.
    Returns a FieldRecord with value, source, method, confidence, and audit entries.
    """
    max_retries = cfg.orchestrator.max_retries_per_field
    chunk_chars = cfg.orchestrator.relevant_chunk_chars
    max_chunks = cfg.orchestrator.max_chunks_per_field

    # Collect results from multiple sources to check cross-source agreement
    source_results: list[tuple[Any, str]] = []  # (value, method)

    # ── Strategy 1: Direct extraction from document ──────────────────────────
    extraction_result: ExtractionResult | None = None
    page_no = None

    if doc.doc_type == "pdf":
        chunks = get_chunks_for_field(doc, field_name, chunk_chars, max_chunks)
        for chunk_info in chunks:
            attempt_result = document_agent.extract_from_text(
                field_name=field_name,
                field_def=field_def,
                text_chunk=chunk_info["text"],
                page_no=chunk_info["page_no"],
                source_file=doc.source_file,
            )
            page_no = chunk_info["page_no"]

            audit.log(
                field=field_name,
                agent="document_agent",
                action="extract_attempt",
                input_summary=f"PDF chunk from page {page_no} ({len(chunk_info['text'])} chars)",
                output_summary=f"value={attempt_result.value!r}, span='{attempt_result.source_span[:60]}'",
                result="success" if attempt_result.value is not None else "failed",
            )

            if attempt_result.value is not None:
                extraction_result = attempt_result
                break  # found something — move to validation

    elif doc.doc_type == "excel":
        attempt_result = excel_agent.extract_from_excel(
            field_name=field_name,
            field_def=field_def,
            doc=doc,
        )
        audit.log(
            field=field_name,
            agent="excel_agent",
            action="extract_attempt",
            input_summary=f"Excel headers: {doc.raw_headers}",
            output_summary=f"value={attempt_result.value!r}, col='{attempt_result.column_name}'",
            result="success" if attempt_result.value is not None else "failed",
        )
        if attempt_result.value is not None:
            extraction_result = attempt_result

    # ── Validate the directly extracted value ────────────────────────────────
    if extraction_result is not None and extraction_result.value is not None:
        val_result = validate_field(
            value=extraction_result.value,
            field_def=field_def,
            unit_found=extraction_result.unit_found,
        )
        audit.log(
            field=field_name,
            agent="validation",
            action="validate",
            input_summary=f"value={extraction_result.value!r}, unit={extraction_result.unit_found!r}",
            output_summary=val_result.reason,
            result="success" if val_result.passed else "failed",
        )

        if val_result.passed:
            final_value = val_result.converted_value if val_result.converted_value is not None else extraction_result.value
            source_results.append((final_value, "direct"))

            method = "direct_text" if doc.doc_type == "pdf" else "direct_excel"
            confidence = cfg.compute_confidence(method, in_range=True)

            source_str = _build_source_string(extraction_result, doc)
            return FieldRecord(
                value=final_value,
                unit=field_def.get("unit"),
                source=source_str,
                method=method,
                confidence=confidence,
                in_range=True,
                flagged=False,
                status="ok",
                audit_entries=audit.entries_for_field(field_name),
            )
        else:
            # Out of range — cap confidence but still record it
            audit.log(
                field=field_name,
                agent="orchestrator",
                action="flag_for_review",
                input_summary=f"value={extraction_result.value!r} failed validation",
                output_summary=f"reason: {val_result.reason}",
                result="flagged",
            )

    # ── Strategy 2: RAG-grounded extraction ──────────────────────────────────
    audit.log(
        field=field_name,
        agent="orchestrator",
        action="rag_fallback",
        input_summary=f"direct extraction failed or invalid for '{field_name}'",
        output_summary="querying vector store for similar products",
        result="skipped" if vector_store.get_collection_count(category) == 0 else "attempting",
    )

    rag_results = vector_store.find_similar(
        category=category,
        query_text=f"{field_name.replace('_', ' ')} {field_def.get('unit', '')}",
    )
    rag_docs = rag_results.get("documents", [[]])[0]

    if rag_docs:
        # Use first available chunk for RAG-grounded re-extraction
        if doc.doc_type == "pdf":
            chunks = get_chunks_for_field(doc, field_name, chunk_chars, 1)
            chunk_text = chunks[0]["text"] if chunks else doc.text[:chunk_chars]
            page_no = chunks[0]["page_no"] if chunks else None
        else:
            chunk_text = doc.text[:chunk_chars]
            page_no = None

        rag_result = document_agent.extract_from_text_with_rag_context(
            field_name=field_name,
            field_def=field_def,
            text_chunk=chunk_text,
            rag_documents=rag_docs,
            page_no=page_no,
        )

        audit.log(
            field=field_name,
            agent="document_agent+rag",
            action="extract_attempt",
            input_summary=f"RAG context: {len(rag_docs)} similar products",
            output_summary=f"value={rag_result.value!r}",
            result="success" if rag_result.value is not None else "failed",
        )

        if rag_result.value is not None:
            val_result = validate_field(
                value=rag_result.value,
                field_def=field_def,
                unit_found=rag_result.unit_found,
            )
            audit.log(
                field=field_name,
                agent="validation",
                action="validate",
                input_summary=f"RAG value={rag_result.value!r}",
                output_summary=val_result.reason,
                result="success" if val_result.passed else "failed",
            )

            final_value = val_result.converted_value if val_result.converted_value is not None else rag_result.value
            confidence = cfg.compute_confidence("rag_inferred", in_range=val_result.passed)
            source_str = _build_source_string(rag_result, doc) + " [via RAG]"

            return FieldRecord(
                value=final_value,
                unit=field_def.get("unit"),
                source=source_str,
                method="rag_inferred",
                confidence=confidence,
                in_range=val_result.passed,
                flagged=True,   # RAG results always flagged for human review
                status="needs_review",
                audit_entries=audit.entries_for_field(field_name),
            )

    # ── Strategy 3: Nothing worked — flag for human review ───────────────────
    audit.log(
        field=field_name,
        agent="orchestrator",
        action="flag_for_review",
        input_summary="all extraction strategies exhausted",
        output_summary="field marked as not_found, needs human review",
        result="flagged",
    )

    return FieldRecord(
        value=None,
        unit=field_def.get("unit"),
        source="",
        method="not_found",
        confidence=0.0,
        in_range=True,
        flagged=True,
        status="not_found",
        audit_entries=audit.entries_for_field(field_name),
    )


def _build_source_string(result: ExtractionResult, doc: IngestedDocument) -> str:
    """Build a human-readable source citation string."""
    filename = Path(doc.source_file).name
    if result.page_number:
        return f"{filename} p.{result.page_number}"
    if result.column_name:
        return f"{filename} col '{result.column_name}'"
    return filename


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def process_document(
    source_file: str,
    category: str,
    origin_tag: str = "real_manufacturer",
) -> tuple[ProductRecord, AuditLogger]:
    """
    Process a single document and return a structured ProductRecord.

    Args:
        source_file: Path to the PDF, Excel, or CSV file
        category: Schema category name (must match a file in data/schemas/)
        origin_tag: Provenance tag for the data

    Returns:
        (ProductRecord, AuditLogger) — the structured record and its full audit trail
    """
    from src.ingestion.pdf_reader import ingest_pdf
    from src.ingestion.excel_reader import ingest_excel

    # ── Load schema ──────────────────────────────────────────────────────────
    schema = load_schema(category)
    fields_def: dict = schema.get("fields", {})

    # ── Ingest document ──────────────────────────────────────────────────────
    path = Path(source_file)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        doc = ingest_pdf(source_file, origin_tag)
    elif suffix in (".xlsx", ".xls", ".csv"):
        doc = ingest_excel(source_file, origin_tag)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    # ── Set up audit logger ──────────────────────────────────────────────────
    audit = AuditLogger()
    audit.log(
        field="__pipeline__",
        agent="orchestrator",
        action="start",
        input_summary=f"file={path.name}, category={category}, origin={origin_tag}",
        output_summary=f"schema has {len(fields_def)} fields, model={cfg.ollama.text_model}",
        result="success",
    )

    # ── Process each field ───────────────────────────────────────────────────
    field_records: dict[str, FieldRecord] = {}
    field_count = min(len(fields_def), cfg.orchestrator.max_fields_per_product)

    for field_name, field_def in list(fields_def.items())[:field_count]:
        print(f"  [{field_name}] extracting ...", end=" ", flush=True)
        field_record = _process_field(field_name, field_def, doc, category, audit)
        field_records[field_name] = field_record

        status_icon = "✓" if field_record.status == "ok" else ("?" if field_record.status == "needs_review" else "✗")
        print(f"{status_icon} value={field_record.value!r}  conf={field_record.confidence:.2f}")

    # ── Compute completeness stats ────────────────────────────────────────────
    total = len(field_records)
    filled = sum(1 for f in field_records.values() if f.value is not None)
    flagged = sum(1 for f in field_records.values() if f.flagged)
    completeness = round(filled / total * 100, 1) if total > 0 else 0.0

    # ── Determine overall status ─────────────────────────────────────────────
    if flagged == 0 and filled == total:
        status = "complete"
    elif filled == 0:
        status = "needs_review"
    else:
        status = "partial"

    audit.log(
        field="__pipeline__",
        agent="orchestrator",
        action="complete",
        input_summary=f"processed {total} fields",
        output_summary=f"filled={filled}, flagged={flagged}, completeness={completeness}%",
        result="success",
    )

    # ── Build final record ────────────────────────────────────────────────────
    record = ProductRecord(
        category=category,
        origin_tag=origin_tag,
        source_file=str(path.resolve()),
        fields=field_records,
        status=status,
        total_fields=total,
        filled_fields=filled,
        flagged_fields=flagged,
        completeness_pct=completeness,
    )

    return record, audit


def save_record(record: ProductRecord, audit: AuditLogger) -> tuple[Path, Path]:
    """Save the product record and its audit trail to disk. Returns (record_path, audit_path)."""
    output_dir = Path(cfg.paths.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    record_path = output_dir / f"{record.record_id}_{record.category}.json"
    audit_path  = output_dir / f"{record.record_id}_{record.category}_audit.json"

    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record.model_dump(), f, indent=2)

    audit.save(audit_path)

    return record_path, audit_path
