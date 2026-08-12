"""
test_backend.py
Smoke test for all backend modules — run before starting the API server.
Expected output: every line prints OK with real values, ends with PASS.
"""
import sys, json
from pathlib import Path

PASS = True

def check(label, condition, detail=""):
    global PASS
    icon = "OK" if condition else "FAIL"
    if not condition:
        PASS = False
    print(f"  [{icon}] {label}" + (f"  -- {detail}" if detail else ""))
    return condition

print("=" * 60)
print("  UniHack Backend Smoke Test")
print("=" * 60)

# 1. Config
print("\n[1] Config")
try:
    from src.config import cfg
    check("config loaded", True, f"model={cfg.ollama.text_model}")
    check("max_retries", cfg.orchestrator.max_retries_per_field == 2)
    check("schemas_dir exists", Path(cfg.paths.schemas_dir).exists())
except Exception as e:
    check("config", False, str(e)); sys.exit(1)

# 2. Models
print("\n[2] Models")
try:
    from src.models import ProductRecord, FieldRecord, AuditEntry, ExtractionResult, IngestedDocument
    check("all models import", True)
    fr = FieldRecord(value=6.0, unit="mm", source="test.pdf p.1", method="direct_text", confidence=0.85)
    check("FieldRecord instantiation", fr.value == 6.0)
except Exception as e:
    check("models", False, str(e))

# 3. Audit logger
print("\n[3] Audit Logger")
try:
    from src.audit import AuditLogger
    a = AuditLogger()
    a.log("bore_diameter","test_agent","extract_attempt","PDF chunk","value=6.0","success")
    a.log("bore_diameter","validation","validate","value=6.0","passed","success")
    check("audit logger", len(a.all_entries()) == 2)
    check("field filter", len(a.entries_for_field("bore_diameter")) == 2)
except Exception as e:
    check("audit", False, str(e))

# 4. Validation
print("\n[4] Schema Validator")
try:
    from src.validation.schema_validator import validate_field
    schema = json.load(open("data/schemas/ball_bearing.json"))
    fd = schema["fields"]["bore_diameter"]
    r1 = validate_field(6.0, fd)
    check("bore=6mm in range [0.5,400]", r1.passed, r1.reason)
    r2 = validate_field(9999.0, fd)
    check("bore=9999mm out of range", not r2.passed, r2.reason)
    r3 = validate_field(None, fd)
    check("null value fails", not r3.passed)
    # Unit conversion
    fd_m = {"type": "number", "unit": "mm", "min": 0.5, "max": 400.0}
    r4 = validate_field(0.006, fd_m, unit_found="m")
    check("0.006m converts to 6mm", r4.passed, f"converted={r4.converted_value}")
    # Enum validation
    fd_mat = schema["fields"]["material"]
    r5 = validate_field("chrome_steel", fd_mat)
    check("chrome_steel in enum", r5.passed)
    r6 = validate_field("titanium", fd_mat)
    check("titanium not in enum", not r6.passed)
except Exception as e:
    check("validation", False, str(e))

# 5. PDF Reader
print("\n[5] PDF Reader")
try:
    from src.ingestion.pdf_reader import ingest_pdf, get_chunks_for_field
    pdf_path = "data/raw/real_manufacturer/Timken-Deep-Groove-Ball-Bearings.pdf"
    doc = ingest_pdf(pdf_path, "real_manufacturer")
    check("pdf ingest", len(doc.pages) > 0, f"pages={len(doc.pages)}")
    check("text extracted", len(doc.text) > 100, f"chars={len(doc.text)}")
    check("page numbers tracked", doc.pages[0]["page_no"] == 1)
    chunks = get_chunks_for_field(doc, "bore_diameter", 2000, 2)
    check("bore_diameter chunks found", len(chunks) > 0, f"chunks={len(chunks)}")
    check("chunk has page_no", "page_no" in chunks[0])
    check("chunk has text", len(chunks[0]["text"]) > 10)
except Exception as e:
    check("pdf_reader", False, str(e))

# 6. Excel Reader
print("\n[6] Excel Reader")
try:
    from src.ingestion.excel_reader import ingest_excel
    # Create a small test CSV
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("Part Number,Bore Diameter (mm),Outer Dia (mm),Width mm,Material\n")
        f.write("626,6,19,6,chrome steel\n")
        f.write("6000,10,26,8,chrome steel\n")
        tmp = f.name
    doc_xl = ingest_excel(tmp, "team_assembled")
    check("excel ingest", len(doc_xl.raw_rows) == 2)
    check("headers preserved", "Bore Diameter (mm)" in doc_xl.raw_headers)
    check("rows as dicts", "Bore Diameter (mm)" in doc_xl.raw_rows[0])
    os.unlink(tmp)
except Exception as e:
    check("excel_reader", False, str(e))

# 7. Excel Agent (header reconciliation)
print("\n[7] Excel Agent — Header Reconciliation")
try:
    from src.agents.excel_agent import find_best_column
    headers = ["Part No", "Bore Dia (mm)", "Outer Diameter mm", "Width", "Material Grade"]
    schema = json.load(open("data/schemas/ball_bearing.json"))
    matched, score = find_best_column(headers, "bore_diameter", schema["fields"]["bore_diameter"])
    check("bore_diameter matched", matched is not None, f"matched='{matched}' score={score:.3f}")
    matched2, score2 = find_best_column(headers, "outer_diameter", schema["fields"]["outer_diameter"])
    check("outer_diameter matched", matched2 is not None, f"matched='{matched2}' score={score2:.3f}")
except Exception as e:
    check("excel_agent", False, str(e))

# 8. Vector Store
print("\n[8] Vector Store (Chroma RAG)")
try:
    from src.retrieval.vector_store import add_product, find_similar, get_collection_count
    add_product(
        "ball_bearing", "smoke_test_626",
        "bearing 626: bore 6mm outer 19mm width 6mm chrome steel",
        {"bore_mm": 6, "outer_mm": 19, "width_mm": 6}
    )
    count = get_collection_count("ball_bearing")
    check("product indexed", count >= 1, f"count={count}")
    results = find_similar("ball_bearing", "small 6mm bore chrome steel bearing")
    docs = results.get("documents", [[]])[0]
    check("similar products retrieved", len(docs) >= 1, f"results={len(docs)}")
except Exception as e:
    check("vector_store", False, str(e))

# 9. Orchestrator wiring
print("\n[9] Orchestrator — Schema Loading")
try:
    from src.orchestrator import list_categories, load_schema
    cats = list_categories()
    check("categories loaded", len(cats) >= 3, f"categories={cats}")
    for cat in cats:
        s = load_schema(cat)
        check(f"schema '{cat}' valid", "fields" in s and len(s["fields"]) > 0, f"fields={list(s['fields'].keys())[:3]}")
except Exception as e:
    check("orchestrator", False, str(e))

# 10. Ollama connectivity
print("\n[10] Ollama Connectivity")
try:
    import requests
    resp = requests.get(f"{cfg.ollama.base_url}/api/tags", timeout=5)
    if resp.status_code == 200:
        models = [m["name"] for m in resp.json().get("models", [])]
        check("ollama reachable", True, f"models={models}")
        target = cfg.ollama.text_model
        model_present = any(target in m for m in models)
        check(f"model '{target}' loaded", model_present,
              "NOT FOUND — run: ollama pull qwen2.5:7b" if not model_present else "ready")
    else:
        check("ollama reachable", False, f"HTTP {resp.status_code}")
except Exception as e:
    check("ollama reachable", False, f"{e} -- Is Ollama running? Start it first.")

# Summary
print()
print("=" * 60)
if PASS:
    print("  ALL TESTS PASSED -- backend is ready")
    print("  Next: python main.py <pdf_file> <category>")
    print("  API:  python -m uvicorn src.api:app --reload --port 8000")
else:
    print("  SOME TESTS FAILED -- fix errors above before running")
print("=" * 60)
