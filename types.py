from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Document:
    doc_id: str           # e.g. "passwords.md"
    source_path: str      # e.g. "data/corpus/passwords.md"
    text: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str         # e.g. "doc:passwords.md#chunk:0"
    doc_id: str
    idx: int
    text: str
    meta: dict[str, Any]
