"""
src/ingestion/pdf_reader.py
Reads PDF files and extracts text with page-level tracking.
Returns page-numbered chunks so every extracted value can be cited to a page.
"""
from __future__ import annotations
import re
from pathlib import Path
import fitz  # PyMuPDF
from src.models import IngestedDocument


# ── Field keyword synonyms ─────────────────────────────────────────────────
# Maps canonical schema field names to keywords that appear near those values in docs.
# This is NOT hardcoding field logic — it's a search hint table, fully overridable.
FIELD_KEYWORDS: dict[str, list[str]] = {
    "bore_diameter":        ["bore", "bore diameter", "bore dia", "inner diameter", "d mm", "d =", " d "],
    "outer_diameter":       ["outer diameter", "outside diameter", "OD", "outer dia", "D mm", "D =", " D "],
    "width":                ["width", "thickness", "B mm", "B =", "face width"],
    "load_rating_dynamic":  ["dynamic load", "dynamic capacity", "basic dynamic", "C =", "C kN", " C "],
    "load_rating_static":   ["static load", "static capacity", "basic static", "C0", "C₀", "C0 kN"],
    "material":             ["material", "steel", "stainless", "chrome", "ceramic", "brass"],
    "flow_rate":            ["flow rate", "capacity", "Q =", "Q [m", "m3/h", "m³/h"],
    "head":                 ["head", "H =", "H [m", "total head", "pump head", "Hmax"],
    "power":                ["power", "motor power", "P =", "kW", "shaft power"],
    "rated_current":        ["rated current", "In =", "nominal current", "In:", "A "],
    "rated_voltage":        ["rated voltage", "Ue", "voltage", "VAC", "VDC", "V AC"],
    "breaking_capacity":    ["breaking capacity", "Icu", "Ics", "kA", "short-circuit"],
    "poles":                ["pole", "3P", "4P", "3-pole", "4-pole"],
    "max_operating_temperature": ["temperature", "temp", "°C", "operating temp"],
    "certification":        ["ISO", "CE", "ABMA", "certif", "standard"],
}


def _extract_relevant_chunks(
    full_text: str,
    field_name: str,
    chunk_chars: int,
    max_chunks: int,
) -> list[tuple[str, int]]:
    """
    Find text windows most likely to contain the value for field_name.
    Returns list of (chunk_text, approx_char_position).
    Falls back to the first chunk_chars of the document if no keywords match.
    """
    keywords = FIELD_KEYWORDS.get(field_name, [field_name.replace("_", " ")])
    found_positions: list[int] = []

    for kw in keywords:
        for m in re.finditer(re.escape(kw), full_text, re.IGNORECASE):
            found_positions.append(m.start())
        if len(found_positions) >= max_chunks * 3:
            break  # enough hits

    if not found_positions:
        # No keyword match — return the beginning of the document
        return [(full_text[:chunk_chars], 0)]

    # De-duplicate and sort
    found_positions = sorted(set(found_positions))

    # Merge overlapping windows
    chunks: list[tuple[str, int]] = []
    last_end = -1
    for pos in found_positions[:max_chunks * 2]:
        start = max(0, pos - 200)  # 200 chars of context before keyword
        end = min(len(full_text), start + chunk_chars)
        if start < last_end:
            continue  # overlaps with previous chunk
        chunks.append((full_text[start:end], start))
        last_end = end
        if len(chunks) >= max_chunks:
            break

    return chunks if chunks else [(full_text[:chunk_chars], 0)]


def ingest_pdf(path: str | Path, origin_tag: str) -> IngestedDocument:
    """
    Read a PDF and return an IngestedDocument with:
    - full concatenated text
    - per-page text list (for page citation)
    """
    path = Path(path)
    doc = fitz.open(str(path))

    pages: list[dict] = []
    full_text_parts: list[str] = []

    for page_no, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({"page_no": page_no, "text": text})
        full_text_parts.append(text)

    doc.close()
    full_text = "\n".join(full_text_parts)

    return IngestedDocument(
        doc_id=path.stem,
        doc_type="pdf",
        origin_tag=origin_tag,
        source_file=str(path),
        text=full_text,
        pages=pages,
    )


def get_chunks_for_field(
    doc: IngestedDocument,
    field_name: str,
    chunk_chars: int,
    max_chunks: int,
) -> list[dict]:
    """
    Return the most relevant text chunks for extracting a specific field.
    Each chunk dict: {text, page_no, char_offset}
    """
    keywords = FIELD_KEYWORDS.get(field_name, [field_name.replace("_", " ")])
    results: list[dict] = []
    seen_pages: set[int] = set()

    # Search page by page (gives us accurate page numbers for citations)
    for page_info in doc.pages:
        page_no = page_info["page_no"]
        page_text = page_info["text"]

        for kw in keywords:
            if kw.lower() in page_text.lower():
                if page_no not in seen_pages:
                    results.append({
                        "text": page_text,
                        "page_no": page_no,
                        "char_offset": 0,
                    })
                    seen_pages.add(page_no)
                break  # one chunk per page is enough

        if len(results) >= max_chunks:
            break

    if not results:
        # Fallback: return first max_chunks pages
        for page_info in doc.pages[:max_chunks]:
            results.append({
                "text": page_info["text"],
                "page_no": page_info["page_no"],
                "char_offset": 0,
            })

    # Trim each chunk to chunk_chars
    for r in results:
        r["text"] = r["text"][:chunk_chars]

    return results
