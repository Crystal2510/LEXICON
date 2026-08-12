"""
src/config.py
Single source of truth for all configuration.
Loads config.yaml — no values are hardcoded anywhere else.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel


class OllamaConfig(BaseModel):
    base_url: str
    text_model: str
    vision_model: str
    timeout_seconds: int
    ollama_exe: str = ""   # path to ollama CLI executable (used as subprocess fallback)


class OrchestratorConfig(BaseModel):
    max_retries_per_field: int
    max_fields_per_product: int
    relevant_chunk_chars: int
    max_chunks_per_field: int


class ConfidenceConfig(BaseModel):
    direct_text: float
    direct_excel: float
    direct_image: float
    rag_inferred: float
    human_verified: float
    out_of_range_cap: float
    cross_source_bonus: float


class RetrievalConfig(BaseModel):
    n_results: int
    embedding_model: str
    min_results_for_inference: int


class PathsConfig(BaseModel):
    schemas_dir: str
    output_dir: str
    chroma_dir: str


class ApiConfig(BaseModel):
    host: str
    port: int
    cors_origins: list[str]


class AppConfig(BaseModel):
    ollama: OllamaConfig
    orchestrator: OrchestratorConfig
    confidence: ConfidenceConfig
    retrieval: RetrievalConfig
    paths: PathsConfig
    api: ApiConfig

    def compute_confidence(
        self,
        method: str,
        in_range: bool = True,
        cross_source_agreement: bool = False,
    ) -> float:
        """
        Transparent rule-based confidence score.
        Fully explainable in one sentence:
          base = method_score; cap at out_of_range_cap if invalid; +bonus if multi-source agrees.
        """
        base_map = {
            "direct_text":    self.confidence.direct_text,
            "direct_excel":   self.confidence.direct_excel,
            "direct_image":   self.confidence.direct_image,
            "rag_inferred":   self.confidence.rag_inferred,
            "human_verified": self.confidence.human_verified,
        }
        score = base_map.get(method, 0.40)

        if not in_range:
            score = min(score, self.confidence.out_of_range_cap)

        if cross_source_agreement:
            score = min(1.0, score + self.confidence.cross_source_bonus)

        return round(score, 2)


def _find_config_file() -> Path:
    """Walk up from cwd to find config.yaml."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        candidate = parent / "config.yaml"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("config.yaml not found. Run from project root.")


def load_config() -> AppConfig:
    config_path = _find_config_file()
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AppConfig(**raw)


# Module-level singleton — import this everywhere
cfg: AppConfig = load_config()
