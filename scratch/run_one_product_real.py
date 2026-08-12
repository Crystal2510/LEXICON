import sys
import os
import requests
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.ingestion import ingest_pdf
from src.vector_store import find_similar

# ---- Step A: read the real PDF text near the bearing table ----
doc = ingest_pdf("data/raw/real_manufacturer/SKF-Rolling-Bearings.pdf", origin_tag="real_manufacturer")
pos = doc.text.find("Principal dimensions")
text_chunk = doc.text[pos:pos+3000]

# ---- Step B: ask the AI model for BOTH bore and outer diameter, not just one ----
prompt = f"""Below is messy text from a bearing catalog PDF. Find the bearing named "626".
Report its bore diameter AND outer diameter separately, in millimeters.

Text:
---
{text_chunk}
---
Answer ONLY in this exact JSON format, nothing else:
{{"bore_mm": <number>, "outer_mm": <number>}}
If you cannot find both values, respond: {{"bore_mm": null, "outer_mm": null}}
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.1:8b", "prompt": prompt, "stream": False}
)

raw_answer = response.json()["response"]
print(f"Raw AI response: {raw_answer}\n")

try:
    extracted = json.loads(raw_answer.strip())
except json.JSONDecodeError:
    print("Could not parse AI response as JSON. Stopping here.")
    sys.exit()

bore = extracted.get("bore_mm")
outer = extracted.get("outer_mm")

# ---- Step C: validate ----
if bore is None or outer is None:
    print("AI could not find both values directly. Falling back to RAG immediately.")
    is_valid = False
else:
    print(f"Direct extraction result: bore = {bore}mm, outer = {outer}mm")
    is_valid = bore < outer
    print(f"Validation check (bore < outer?): {is_valid}")

# ---- Step D: RAG fallback if invalid or missing ----
if not is_valid:
    print("\n⚠️ Validation FAILED or value missing — falling back to RAG.")
    query = "bearing 626 small miniature chrome steel"
    results = find_similar("ball_bearings", query)
    print("Similar bearings found as a hint:")
    for d in results["documents"][0]:
        print(" -", d)
    print("\n→ FIELD STATUS: flagged_for_review")
else:
    print("\n✅ Value accepted, confidence: HIGH")
    print("→ FIELD STATUS: accepted")