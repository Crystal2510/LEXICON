"""
test_e2e.py
End-to-end pipeline test using whatever model is currently loaded in Ollama.
Tests the full flow: ingest → orchestrator → validate → save → verify output.
"""
import sys, json
from pathlib import Path

print("=" * 60)
print("  UniHack End-to-End Pipeline Test")
print("=" * 60)

from src.config import cfg
from src.orchestrator import process_document, save_record

# Use a small PDF for speed
PDF = "data/raw/real_manufacturer/Timken-Deep-Groove-Ball-Bearings.pdf"
CATEGORY = "ball_bearing"

print(f"\n  File    : {Path(PDF).name}")
print(f"  Category: {CATEGORY}")
print(f"  Model   : {cfg.ollama.text_model}")
print()

record, audit = process_document(PDF, CATEGORY, origin_tag="real_manufacturer")
record_path, audit_path = save_record(record, audit)

print()
print("=" * 60)
print("  RESULTS")
print("=" * 60)
print(f"  Record ID     : {record.record_id}")
print(f"  Status        : {record.status}")
print(f"  Completeness  : {record.completeness_pct}%")
print(f"  Filled        : {record.filled_fields}/{record.total_fields}")
print(f"  Flagged       : {record.flagged_fields}")
print()

print(f"  {'Field':<28} {'Value':<22} {'Conf':>5}  {'Method':<16}  Source")
print(f"  {'-'*28} {'-'*22} {'-'*5}  {'-'*16}  {'-'*35}")
for fname, frec in record.fields.items():
    val = f"{frec.value}" if frec.value is not None else "NOT FOUND"
    if frec.unit and frec.value is not None:
        val += f" {frec.unit}"
    icon = "OK" if frec.status=="ok" else ("??" if frec.status=="needs_review" else "XX")
    print(f"  [{icon}] {fname:<24} {val:<22} {frec.confidence:>5.2f}  {frec.method:<16}  {frec.source[:35]}")

print()
print(f"  Record saved : {record_path}")
print(f"  Audit saved  : {audit_path}")

# Verify output files
assert record_path.exists(), "Record file not saved!"
assert audit_path.exists(), "Audit file not saved!"
saved = json.load(open(record_path))
assert saved["record_id"] == record.record_id
assert saved["category"] == CATEGORY
assert "fields" in saved
print()
print("  [OK] Record file is valid JSON with correct structure")
print("  [OK] Audit file saved")

audit_data = json.load(open(audit_path))
print(f"  [OK] Audit trail has {len(audit_data)} decision entries")

# Show first 5 audit entries
print("\n  AUDIT TRAIL (first 5 entries):")
for entry in audit_data[:5]:
    print(f"    step={entry['step']}  agent={entry['agent']:<20}  action={entry['action']:<20}  result={entry['result']}")

print()
print("=" * 60)
print("  END-TO-END TEST COMPLETE")
print("=" * 60)
