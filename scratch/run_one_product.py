import sys
import os

# This finds the Unilog folder no matter where the script is run from
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.ingestion import ingest_pdf
from src.vector_store import find_similar

# Step A: try direct extraction (we already know this can be unreliable on messy tables)
doc = ingest_pdf("data/raw/real_manufacturer/SKF-Rolling-Bearings.pdf", origin_tag="real_manufacturer")

extracted_value = 19  # pretend this is what direct extraction returned for bearing 626 (we know this is WRONG, from earlier)
known_correct_bore_range = (1, 500)  # from your schema file

# Step B: validate — does it make sense?
outer_diameter = 19  # also extracted directly
is_valid = extracted_value < outer_diameter  # bore must always be smaller than outer diameter

print(f"Direct extraction result: bore = {extracted_value}mm, outer = {outer_diameter}mm")
print(f"Validation check (bore < outer?): {is_valid}")

if not is_valid:
    print("\n⚠️ Validation FAILED — bore cannot equal/exceed outer diameter. Falling back to RAG.")
    query = f"bearing outer diameter {outer_diameter}mm chrome steel"
    results = find_similar("ball_bearings", query)
    print("Similar bearings found as a hint:")
    for d in results["documents"][0]:
        print(" -", d)
    print("\n→ This field should be FLAGGED FOR HUMAN REVIEW, not auto-filled.")
else:
    print("\n✅ Value accepted, confidence: HIGH")