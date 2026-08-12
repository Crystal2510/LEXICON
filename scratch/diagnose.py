import json, requests
from src.config import cfg

# ── 1. Read audit log to see raw LLM responses ───────────────────────────
import os
output_dir = "data/output"
audit_files = [f for f in os.listdir(output_dir) if "_audit.json" in f]
if audit_files:
    with open(os.path.join(output_dir, sorted(audit_files)[-1])) as f:
        audit = json.load(f)
    print("=== AUDIT LOG (all entries) ===")
    for e in audit:
        print(f"  step={e['step']}  agent={e['agent']}  result={e['result']}")
        print(f"    in : {e['input_summary'][:120]}")
        print(f"    out: {e['output_summary'][:200]}")
        print()

# ── 2. Direct Ollama connectivity test ───────────────────────────────────
print("\n=== OLLAMA DIRECT TEST ===")
print(f"  URL   : {cfg.ollama.base_url}")
print(f"  Model : {cfg.ollama.text_model}")

# Check what models are available
try:
    tags = requests.get(f"{cfg.ollama.base_url}/api/tags", timeout=5).json()
    models = [m["name"] for m in tags.get("models", [])]
    print(f"  Available models: {models}")
except Exception as e:
    print(f"  ERROR getting models: {e}")

# Try a minimal chat call
try:
    resp = requests.post(
        f"{cfg.ollama.base_url}/api/chat",
        json={
            "model": cfg.ollama.text_model,
            "messages": [{"role": "user", "content": 'Return only this JSON: {"value": 42}'}],
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 50},
        },
        timeout=30,
    )
    print(f"  HTTP status: {resp.status_code}")
    print(f"  Response: {resp.text[:500]}")
except Exception as e:
    print(f"  ERROR calling Ollama: {type(e).__name__}: {e}")

# ── 3. Try with llama3.1 as fallback ─────────────────────────────────────
print("\n=== TESTING WITH llama3.1:8b ===")
try:
    resp2 = requests.post(
        f"{cfg.ollama.base_url}/api/chat",
        json={
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": 'Return only this JSON: {"value": 42}'}],
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 50},
        },
        timeout=30,
    )
    print(f"  HTTP status: {resp2.status_code}")
    print(f"  Response: {resp2.text[:300]}")
except Exception as e:
    print(f"  ERROR: {e}")
