"""
scratch/test_prompt_build.py
Quick sanity check: can we build a valid prompt without KeyError?
Also tests the subprocess call with a very short warmup prompt.
"""
import json, sys
sys.path.insert(0, ".")

print("=== Prompt build test ===")
from src.agents.document_agent import (
    _build_field_prompt_args, USER_PROMPT_TEMPLATE,
    USER_PROMPT_WITH_CONTEXT, _call_ollama_subprocess, SYSTEM_PROMPT
)
import json

schema = json.load(open("data/schemas/ball_bearing.json"))

# Test 1: bore_diameter (number with min/max, no enum)
fd = schema["fields"]["bore_diameter"]
args = _build_field_prompt_args("bore_diameter", fd)
args["text_chunk"] = "Bore diameter: 6 mm, Outer diameter: 19 mm"
prompt = USER_PROMPT_TEMPLATE.format(**args)
print("[OK] bore_diameter prompt built, length:", len(prompt))
print("     preview:", prompt[:150].replace("\n","\\n"))

# Test 2: material (string with enum)
fd2 = schema["fields"]["material"]
args2 = _build_field_prompt_args("material", fd2)
args2["text_chunk"] = "Material: chrome steel, AISI 52100"
prompt2 = USER_PROMPT_TEMPLATE.format(**args2)
print("[OK] material prompt built, length:", len(prompt2))
print("     enum_hint:", args2["field_enum_hint"])

# Test 3: RAG prompt
args3 = _build_field_prompt_args("bore_diameter", fd)
args3["text_chunk"] = "Bore: 6mm"
args3["rag_context"] = "bearing 626: bore 6mm"
prompt3 = USER_PROMPT_WITH_CONTEXT.format(**args3)
print("[OK] RAG prompt built, length:", len(prompt3))

print()
print("=== Subprocess test (minimal prompt, short timeout) ===")
print("Sending: 'What is 2+2? Reply with just the number.'")
try:
    import subprocess, time
    from src.config import cfg
    from pathlib import Path

    exe = cfg.ollama.ollama_exe.replace("/", "\\")
    t0 = time.time()
    result = subprocess.run(
        [exe, "run", cfg.ollama.text_model],
        input="What is 2+2? Reply with just the number.",
        capture_output=True, text=True, timeout=300,
        encoding="utf-8", errors="replace"
    )
    elapsed = time.time() - t0
    out = result.stdout.strip()
    err = result.stderr.strip()
    print(f"  Time: {elapsed:.1f}s")
    print(f"  stdout: {repr(out[:200])}")
    if err:
        print(f"  stderr: {err[:200]}")
    if out:
        print("[OK] Subprocess ollama call worked!")
    else:
        print("[FAIL] No output from subprocess")
except subprocess.TimeoutExpired:
    print("[FAIL] Subprocess timed out")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
