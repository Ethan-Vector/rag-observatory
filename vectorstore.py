from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from typing import Iterable

from .types import Chunk


def cosine(a: list[float], b: list[float]) -> float:
    # vectors are already normalized in embedder; keep generic
    s = 0.0
    for x, y in zip(a, b):
        s += x * y
    return float(s)


@dataclass
class VectorStore:
    path: str

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    meta_json TEXT NOT NULL,
                    embedding_json TEXT NOT NULL
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc ON chunks(doc_id);")

    def upsert_chunks(self, chunks: Iterable[Chunk], embeddings: dict[str, list[float]]) -> int:
        n = 0
        with self.connect() as conn:
            for c in chunks:
                emb = embeddings[c.chunk_id]
                conn.execute(
                    """
                    INSERT INTO chunks(chunk_id, doc_id, idx, text, meta_json, embedding_json)
                    VALUES(?,?,?,?,?,?)
                    ON CONFLICT(chunk_id) DO UPDATE SET
                      doc_id=excluded.doc_id,
                      idx=excluded.idx,
                      text=excluded.text,
                      meta_json=excluded.meta_json,
                      embedding_json=excluded.embedding_json;
                    """
                    ,
                    (c.chunk_id, c.doc_id, c.idx, c.text, json.dumps(c.meta), json.dumps(emb)),
                )
                n += 1
        return n

    def all_chunks(self) -> list[Chunk]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT chunk_id, doc_id, idx, text, meta_json FROM chunks ORDER BY doc_id, idx"
            ).fetchall()
        out: list[Chunk] = []
        for chunk_id, doc_id, idx, text, meta_json in rows:
            out.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    idx=int(idx),
                    text=text,
                    meta=json.loads(meta_json),
                )
            )
        return out

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        """
        Baseline: full-scan cosine in SQLite layer.
        OK per demo e corpora piccoli.
        In prod: HNSW/FAISS/pgvector.
        """
        with self.connect() as conn:
            rows = conn.execute("SELECT chunk_id, doc_id, idx, text, meta_json, embedding_json FROM chunks").fetchall()

        scored = []
        for chunk_id, doc_id, idx, text, meta_json, emb_json in rows:
            emb = json.loads(emb_json)
            s = cosine(query_embedding, emb)
            scored.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "idx": int(idx),
                    "text": text,
                    "meta": json.loads(meta_json),
                    "score": float(s),
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
