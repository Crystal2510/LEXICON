"""
src/ingestion/excel_reader.py
Reads Excel/CSV files into an IngestedDocument.
Preserves raw column headers — reconciliation happens in excel_agent, not here.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from src.models import IngestedDocument


def ingest_excel(path: str | Path, origin_tag: str) -> IngestedDocument:
    """
    Read an Excel (.xlsx, .xls) or CSV file.
    Returns IngestedDocument with:
    - raw_rows: list of dicts with original header names
    - raw_headers: the original column headers as-is
    - text: a human-readable text summary (for embedding / LLM context)
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(str(path), dtype=str, keep_default_na=False)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(str(path), dtype=str, keep_default_na=False)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Expected .csv, .xlsx, or .xls")

    raw_headers = list(df.columns)
    raw_rows = df.to_dict(orient="records")

    # Build a text representation for LLM context
    text_lines = [f"Columns: {', '.join(raw_headers)}", ""]
    for i, row in enumerate(raw_rows[:50]):  # first 50 rows for context
        line = " | ".join(f"{k}: {v}" for k, v in row.items() if str(v).strip())
        if line:
            text_lines.append(f"Row {i+1}: {line}")

    full_text = "\n".join(text_lines)

    return IngestedDocument(
        doc_id=path.stem,
        doc_type="excel",
        origin_tag=origin_tag,
        source_file=str(path),
        text=full_text,
        raw_rows=raw_rows,
        raw_headers=raw_headers,
    )
