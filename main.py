#!/usr/bin/env python
"""
main.py — CLI entry point for local testing.

Usage:
  python main.py <file_path> <category> [origin_tag]

Examples:
  python main.py data/raw/real_manufacturer/SKF-Rolling-Bearings.pdf ball_bearing
  python main.py data/raw/real_manufacturer/Grundfos-CR-CRI-CRN-Data-Booklet.pdf centrifugal_pump
  python main.py data/raw/real_manufacturer/Schneider-ComPacT-NSX-User-Guide.pdf circuit_breaker
"""
from __future__ import annotations
import sys
import json
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    file_path  = sys.argv[1]
    category   = sys.argv[2]
    origin_tag = sys.argv[3] if len(sys.argv) > 3 else "real_manufacturer"

    from src.orchestrator import process_document, save_record, list_categories

    # Validate inputs
    if not Path(file_path).exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    available = list_categories()
    if category not in available:
        print(f"ERROR: Unknown category '{category}'")
        print(f"Available categories: {available}")
        sys.exit(1)

    print("=" * 60)
    print(f"  UniHack Product Intelligence System")
    print(f"  File    : {Path(file_path).name}")
    print(f"  Category: {category}")
    print(f"  Origin  : {origin_tag}")
    print("=" * 60)

    from src.config import cfg
    print(f"  Model   : {cfg.ollama.text_model}  (from config.yaml)")
    print()

    # Run pipeline
    record, audit = process_document(file_path, category, origin_tag)
    record_path, audit_path = save_record(record, audit)

    # Print summary
    print()
    print("=" * 60)
    print(f"  RESULT SUMMARY")
    print("=" * 60)
    print(f"  Record ID     : {record.record_id}")
    print(f"  Status        : {record.status.upper()}")
    print(f"  Completeness  : {record.completeness_pct}%")
    print(f"  Filled        : {record.filled_fields}/{record.total_fields} fields")
    print(f"  Flagged       : {record.flagged_fields} fields need human review")
    print()
    print("  FIELD DETAILS:")
    print(f"  {'Field':<28} {'Value':<20} {'Conf':>6}  {'Status':<14}  Source")
    print(f"  {'-'*28} {'-'*20} {'-'*6}  {'-'*14}  {'-'*30}")

    for fname, frec in record.fields.items():
        val_str = str(frec.value)[:19] if frec.value is not None else "NOT FOUND"
        unit_str = f" {frec.unit}" if frec.unit and frec.value is not None else ""
        status_icon = "✓ ok" if frec.status == "ok" else ("? review" if frec.status == "needs_review" else "✗ missing")
        source_short = frec.source[:35] if frec.source else "—"
        print(f"  {fname:<28} {val_str+unit_str:<20} {frec.confidence:>6.2f}  {status_icon:<14}  {source_short}")

    print()
    print(f"  Saved record : {record_path}")
    print(f"  Saved audit  : {audit_path}")
    print("=" * 60)

    if record.flagged_fields > 0:
        print(f"\n  {record.flagged_fields} field(s) flagged for human review.")
        print("  Start the API server to review them:")
        print("    python -m uvicorn src.api:app --reload")
        print(f"  Then PATCH /record/{record.record_id}/field/<field_name>")


if __name__ == "__main__":
    main()
