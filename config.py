from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class EnvSettings(BaseSettings):
    app_host: str = "0.0.0.0"
    app_port: int = 8090
    log_level: str = "INFO"
    config_path: str = "configs/rag.yaml"

    class Config:
        env_file = ".env"
        extra = "ignore"


class ChunkingConfig(BaseModel):
    max_chars: int = 900
    overlap_chars: int = 150
    min_chars: int = 120


class EmbeddingConfig(BaseModel):
    dim: int = 384


class RetrievalConfig(BaseModel):
    top_k: int = 8


class RerankConfig(BaseModel):
    enabled: bool = True
    method: str = "lexical_overlap"
    top_k: int = 5


class AnsweringConfig(BaseModel):
    confidence_threshold: float = 0.18
    max_context_chars: int = 2200


class TracingConfig(BaseModel):
    enabled: bool = True
    traces_dir: str = "traces"


class CorpusConfig(BaseModel):
    root_dir: str = "data/corpus"
    include_globs: list[str] = Field(default_factory=lambda: ["**/*.md", "**/*.txt"])
    encoding: str = "utf-8"


class StorageConfig(BaseModel):
    sqlite_path: str = "ragobs.sqlite"


class RagAppConfig(BaseModel):
    rag: dict[str, Any] = Field(default_factory=dict)
    storage: StorageConfig = StorageConfig()
    corpus: CorpusConfig = CorpusConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    rerank: RerankConfig = RerankConfig()
    answering: AnsweringConfig = AnsweringConfig()
    tracing: TracingConfig = TracingConfig()


@dataclass(frozen=True)
class LoadedConfig:
    config: RagAppConfig
    raw: dict[str, Any]
    version_hash: str


def load_config(path: str) -> LoadedConfig:
    p = Path(path)
    raw_bytes = p.read_bytes()
    raw: dict[str, Any] = yaml.safe_load(raw_bytes) or {}
    version_hash = hashlib.sha256(raw_bytes).hexdigest()[:12]
    config = RagAppConfig.model_validate(raw)
    return LoadedConfig(config=config, raw=raw, version_hash=version_hash)
