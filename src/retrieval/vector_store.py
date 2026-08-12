"""
src/retrieval/vector_store.py
Chroma-backed vector store for RAG enrichment.
- add_product: index a known product as a reference example
- find_similar: retrieve the most similar products for a given query
- add_human_verified: add a human-corrected record as a high-trust reference
"""
from __future__ import annotations
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from src.config import cfg


def _get_collection(category: str):
    """Get or create a Chroma collection for a given product category."""
    chroma_path = str(Path(cfg.paths.chroma_dir).resolve())
    client = chromadb.PersistentClient(path=chroma_path)
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=cfg.retrieval.embedding_model
    )
    return client.get_or_create_collection(
        name=category.replace(" ", "_").lower(),
        embedding_function=emb_fn,
    )


def add_product(
    category: str,
    product_id: str,
    text: str,
    metadata: dict,
) -> None:
    """
    Add a reference product to the vector store.
    text: a human-readable description of the product's fields.
    metadata: key-value pairs of field values (must be str/int/float/bool).
    """
    collection = _get_collection(category)
    # Chroma metadata values must be str/int/float/bool
    safe_meta = {
        k: str(v) if not isinstance(v, (str, int, float, bool)) else v
        for k, v in metadata.items()
    }
    safe_meta["_trust"] = metadata.get("_trust", "reference")
    collection.upsert(ids=[product_id], documents=[text], metadatas=[safe_meta])


def find_similar(
    category: str,
    query_text: str,
    n_results: int | None = None,
) -> dict:
    """
    Retrieve the most similar reference products for a query.
    Returns Chroma query result dict: {ids, documents, metadatas, distances}.
    """
    n = n_results or cfg.retrieval.n_results
    collection = _get_collection(category)

    count = collection.count()
    if count == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    n = min(n, count)  # can't request more than we have
    return collection.query(query_texts=[query_text], n_results=n)


def add_human_verified(
    category: str,
    record_id: str,
    field_name: str,
    corrected_value,
    full_field_text: str,
) -> None:
    """
    Add a human-verified field correction as a high-trust reference.
    Future RAG retrievals will include this — the correction propagates automatically.
    """
    product_id = f"human_{record_id}_{field_name}"
    text = f"{field_name}: {corrected_value}. {full_field_text}"
    metadata = {
        field_name: str(corrected_value),
        "_trust": "human_verified",
        "_record_id": record_id,
        "_field": field_name,
    }
    add_product(category, product_id, text, metadata)


def get_collection_count(category: str) -> int:
    """Return the number of indexed products for a category."""
    return _get_collection(category).count()
