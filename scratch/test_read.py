from src.ingestion import ingest_pdf

doc = ingest_pdf("data/raw/real_manufacturer/SKF-Rolling-Bearings.pdf", origin_tag="real_manufacturer")
print(f"Total characters extracted: {len(doc.text)}")
print("---")
print(doc.text[5000:6500])