from src.ingestion import ingest_pdf

doc = ingest_pdf("data/raw/real_manufacturer/SKF-Rolling-Bearings.pdf", origin_tag="real_manufacturer")

pos = doc.text.find("Principal dimensions")
print(doc.text[pos:pos+3000])