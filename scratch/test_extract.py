import requests
from src.ingestion import ingest_pdf

doc = ingest_pdf("data/raw/real_manufacturer/SKF-Rolling-Bearings.pdf", origin_tag="real_manufacturer")

pos = doc.text.find("Principal dimensions")
text_chunk = doc.text[pos:pos+3000]

prompt = f"""Below is messy text extracted from a bearing catalog PDF. The numbers are
jumbled together because of how the table was extracted, but bearing part numbers
(like 626, 619/6, 635-2RZ) and their dimensions are both present.

Find the bearing named "626" specifically. Report its bore diameter (usually the
first small number listed right after its name, in mm).

Text:
---
{text_chunk}
---
Answer in this exact format: "Bearing 626 bore diameter: <value> mm" or
"Not found" if you genuinely cannot determine it.
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.1:8b", "prompt": prompt, "stream": False}
)

print(response.json()["response"])