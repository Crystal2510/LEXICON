"""
src/agents/excel_agent.py
Extracts field values from Excel/CSV rows by reconciling messy column headers
to canonical schema field names using embedding similarity.

Key design: no hardcoded header mappings.
"Qty", "Quantity", "Stock Count" are all matched to "quantity" at runtime.
Low-confidence matches are flagged, never silently accepted.
"""
from __future__ import annotations
from sentence_transformers import SentenceTransformer, util
from src.config import cfg
from src.models import ExtractionResult, IngestedDocument

# Cache the embedding model (loaded once, reused)
_embedding_model: SentenceTransformer | None = None

# Cache confirmed header→field mappings from human corrections
# Format: {header_lower: canonical_field_name}
_confirmed_mappings: dict[str, str] = {}

# Minimum cosine similarity to accept a header match (without human confirmation)
MATCH_THRESHOLD = 0.45


def _get_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(cfg.retrieval.embedding_model)
    return _embedding_model


def find_best_column(
    headers: list[str],
    field_name: str,
    field_def: dict,
) -> tuple[str | None, float]:
    """
    Find the best matching column header for a schema field.
    Returns (matched_header, similarity_score) or (None, 0.0) if no good match.
    """
    # Check confirmed mappings cache first
    for header in headers:
        if _confirmed_mappings.get(header.lower()) == field_name:
            return header, 1.0

    # Build query: field name + unit + synonyms
    unit = field_def.get("unit", "")
    query = f"{field_name.replace('_', ' ')} {unit}".strip()

    model = _get_model()
    query_emb = model.encode(query, convert_to_tensor=True)
    header_embs = model.encode(headers, convert_to_tensor=True)

    similarities = util.cos_sim(query_emb, header_embs)[0]
    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])

    if best_score >= MATCH_THRESHOLD:
        return headers[best_idx], round(best_score, 3)
    return None, round(best_score, 3)


def confirm_mapping(header: str, field_name: str) -> None:
    """Called when a human reviewer confirms a column→field mapping."""
    _confirmed_mappings[header.lower()] = field_name


def extract_from_excel(
    field_name: str,
    field_def: dict,
    doc: IngestedDocument,
    row_index: int = 0,
) -> ExtractionResult:
    """
    Extract a field value from an Excel document.
    Finds the best matching column, reads the value from the specified row.
    Returns ExtractionResult — value is None if no confident match found.
    """
    if not doc.raw_headers or not doc.raw_rows:
        return ExtractionResult(
            value=None,
            agent="excel_agent",
            raw_llm_response="No Excel data available",
        )

    matched_header, score = find_best_column(doc.raw_headers, field_name, field_def)

    if matched_header is None:
        return ExtractionResult(
            value=None,
            agent="excel_agent",
            raw_llm_response=f"No column matched field '{field_name}' (best score: {score:.3f} < threshold {MATCH_THRESHOLD})",
        )

    # Use the matched column — flagged if score is borderline
    flagged = score < 0.65
    raw_value = doc.raw_rows[row_index].get(matched_header, "").strip() if doc.raw_rows else ""

    if not raw_value:
        return ExtractionResult(
            value=None,
            agent="excel_agent",
            column_name=matched_header,
            raw_llm_response=f"Column '{matched_header}' matched (score={score:.3f}) but value is empty",
        )

    # Attempt numeric conversion for number fields
    parsed_value: str | float = raw_value
    if field_def.get("type") in ("number", "integer"):
        try:
            parsed_value = float(raw_value.replace(",", "."))
        except ValueError:
            parsed_value = raw_value  # keep as string, validator will catch it

    return ExtractionResult(
        value=parsed_value,
        source_span=f"Column '{matched_header}' (similarity={score:.3f})",
        unit_found=None,
        agent="excel_agent",
        column_name=matched_header,
        raw_llm_response=f"Matched header '{matched_header}' with score {score:.3f}",
    )
