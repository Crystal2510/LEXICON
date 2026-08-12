"""
scratch/test_ollama_direct.py
Minimal Ollama test using /api/generate (same endpoint as 'ollama run').
Run this AFTER restarting Ollama to confirm it works.
"""
import requests, json, time

BASE = "http://localhost:11434"

print("=== Ollama Direct Test (using /api/generate) ===\n")

# 1. Check available models
try:
    tags = requests.get(f"{BASE}/api/tags", timeout=10).json()
    models = [m["name"] for m in tags.get("models", [])]
    print(f"Available models: {models}")
except Exception as e:
    print(f"Cannot reach Ollama at {BASE}: {e}")
    print("\nFix: Open a new terminal and run Ollama first:")
    print("  C:\\Users\\Gauri\\AppData\\Local\\Programs\\Ollama\\ollama.exe serve")
    exit(1)

model = "llama3.1:8b"
if model not in models:
    print(f"Model {model} not found. Available: {models}")
    if models:
        model = models[0]
        print(f"Using: {model}")
    else:
        print("No models loaded. Run: ollama pull llama3.1:8b")
        exit(1)

print(f"\nTesting model: {model}")
print("Sending minimal extraction prompt (should respond in <30s)...")

t0 = time.time()
try:
    resp = requests.post(
        f"{BASE}/api/generate",
        json={
            "model": model,
            "prompt": 'Extract from this text: "Bore diameter: 6 mm, Outer diameter: 19 mm"\nReturn ONLY this JSON: {"bore_mm": <number>, "outer_mm": <number>}',
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 80},
        },
        timeout=120,
    )
    elapsed = time.time() - t0
    print(f"Response time: {elapsed:.1f}s")
    print(f"HTTP status: {resp.status_code}")

    if resp.status_code == 200:
        content = resp.json()["response"]
        print(f"Raw response: {content}")

        # Try to parse JSON
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            print(f"\nParsed: bore_mm={parsed.get('bore_mm')}, outer_mm={parsed.get('outer_mm')}")
            print("\n[OK] Ollama is working correctly. Ready to run the full pipeline.")
            print("Next step: python test_e2e.py")
        else:
            print(f"\n[WARN] Got a response but no JSON found. Response: {content[:300]}")
            print("The model responded but isn't following JSON format — prompts may need tuning.")
    else:
        print(f"Error response: {resp.text[:300]}")

except requests.exceptions.ReadTimeout:
    elapsed = time.time() - t0
    print(f"\n[FAIL] Timed out after {elapsed:.0f}s")
    print("\nOllama is not responding to inference requests.")
    print("This usually means Ollama needs to be restarted.")
    print("\nFIX:")
    print("  1. Close/kill any running Ollama processes")
    print("  2. Open a NEW terminal (PowerShell or CMD)")
    print("  3. Run: C:\\Users\\Gauri\\AppData\\Local\\Programs\\Ollama\\ollama.exe serve")
    print("  4. Wait for: 'Listening on 127.0.0.1:11434'")
    print("  5. Then run this test again: python -m scratch.test_ollama_direct")
except Exception as e:
    print(f"[FAIL] Error: {e}")
