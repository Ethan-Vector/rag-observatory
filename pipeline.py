from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .answering import grounded_answer
from .chunking import chunk_document
from .config import LoadedConfig
from .embeddings import Embedder
from .ingest import iter_corpus
from .rerank import rerank_lexical
from .tracing import TraceBundle, Tracer
from .vectorstore import VectorStore


@dataclass
class RagPipeline:
    cfg: LoadedConfig
    store: VectorStore
    embedder: Embedder
    tracer: Tracer

    @classmethod
    def from_config(cls, cfg: LoadedConfig) -> "RagPipeline":
        store = VectorStore(cfg.config.storage.sqlite_path)
        store.init()
        embedder = Embedder(dim=cfg.config.embedding.dim)
        tracer = Tracer(enabled=cfg.config.tracing.enabled, traces_dir=cfg.config.tracing.traces_dir)
        return cls(cfg=cfg, store=store, embedder=embedder, tracer=tracer)

    def ingest(self) -> dict[str, Any]:
        corpus = self.cfg.config.corpus
        chunk_cfg = self.cfg.config.chunking

        n_docs = 0
        all_chunks = []
        for doc in iter_corpus(corpus.root_dir, corpus.include_globs, corpus.encoding):
            n_docs += 1
            chunks = chunk_document(
                doc=doc,
                max_chars=chunk_cfg.max_chars,
                overlap_chars=chunk_cfg.overlap_chars,
                min_chars=chunk_cfg.min_chars,
            )
            all_chunks.extend(chunks)

        embeddings = {c.chunk_id: self.embedder.embed(c.text) for c in all_chunks}
        n_chunks = self.store.upsert_chunks(all_chunks, embeddings)

        return {"docs": n_docs, "chunks": n_chunks, "config_version": self.cfg.version_hash}

    def query(self, route: str, query: str, top_k: Optional[int] = None) -> dict[str, Any]:
        # rewrite: simple normalize
        rewrite = " ".join(query.strip().split())

        k = int(top_k or self.cfg.config.retrieval.top_k)
        q_emb = self.embedder.embed(rewrite)

        retrieval = self.store.search(q_emb, top_k=k)

        rerank = []
        final = retrieval
        if self.cfg.config.rerank.enabled:
            rk = int(self.cfg.config.rerank.top_k)
            rerank = rerank_lexical(rewrite, retrieval, top_k=rk)
            final = rerank

        ans_cfg = self.cfg.config.answering
        ans = grounded_answer(
            query=rewrite,
            passages=final,
            max_context_chars=ans_cfg.max_context_chars,
            threshold=ans_cfg.confidence_threshold,
        )

        trace_id = self.tracer.new_trace_id()
        bundle = TraceBundle(
            trace_id=trace_id,
            ts_ms=self.tracer.now_ms(),
            config_version=self.cfg.version_hash,
            route=route,
            query=query,
            rewrite=rewrite,
            top_k=k,
            retrieval=_slim(retrieval),
            rerank=_slim(rerank),
            decision={"confidence": ans.confidence, "no_answer": ans.no_answer, "citations": ans.citations},
        )
        self.tracer.emit(bundle)

        return {
            "answer": ans.answer,
            "citations": ans.citations,
            "confidence": ans.confidence,
            "no_answer": ans.no_answer,
            "trace_id": trace_id,
        }


def _slim(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for it in items:
        out.append(
            {
                "chunk_id": it.get("chunk_id"),
                "doc_id": it.get("doc_id"),
                "idx": it.get("idx"),
                "score": float(it.get("score", 0.0)),
                "rerank_score": float(it.get("rerank_score", 0.0)) if "rerank_score" in it else None,
            }
        )
    return out
