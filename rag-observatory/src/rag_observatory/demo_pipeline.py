from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .tracing import trace_run


_WORD = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(s: str) -> List[str]:
    return [m.group(0).lower() for m in _WORD.finditer(s)]


@dataclass
class Doc:
    id: str
    text: str


class SimpleRetriever:
    """A tiny token-overlap retriever (offline demo)."""

    def __init__(self, docs: List[Doc]) -> None:
        self.docs = docs
        self.doc_tokens = {d.id: set(_tokenize(d.text)) for d in docs}

    def retrieve(self, query: str, top_k: int = 5) -> List[Doc]:
        q = set(_tokenize(query))
        scored: List[Tuple[float, Doc]] = []
        for d in self.docs:
            overlap = len(q & self.doc_tokens[d.id])
            scored.append((float(overlap), d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:top_k]]


def _load_demo_docs() -> List[Doc]:
    kb = Path(__file__).resolve().parents[2] / "docs" / "knowledge_base"
    docs: List[Doc] = []
    for p in sorted(kb.glob("*.md")):
        docs.append(Doc(id=p.stem, text=p.read_text(encoding="utf-8")))
    return docs


def _mock_generate_answer(query: str, docs: List[Doc]) -> str:
    # Deterministic, no external calls. Summarizes with a silly but stable heuristic.
    if not docs:
        return "I couldn't find anything relevant in the knowledge base."
    first = docs[0].text.strip().splitlines()[0][:120]
    return f"Based on the retrieved context, here's the key point: {first}"


def run_demo(query: str, gold_doc_ids: List[str] | None = None, expected_answer_contains: List[str] | None = None) -> str:
    docs = _load_demo_docs()
    retriever = SimpleRetriever(docs)

    meta = {}
    if gold_doc_ids:
        meta["gold_doc_ids"] = gold_doc_ids
    if expected_answer_contains:
        meta["expected_answer_contains"] = expected_answer_contains

    with trace_run(query=query, meta=meta) as tr:
        with tr.span("retrieve", top_k=5) as sp:
            time.sleep(random.uniform(0.01, 0.05))  # emulate work
            retrieved = retriever.retrieve(query, top_k=5)
            sp.set("retrieved_ids", [d.id for d in retrieved])
            sp.set("retrieved_preview", [d.text[:80] for d in retrieved])

        with tr.span("generate") as sp:
            time.sleep(random.uniform(0.02, 0.08))
            answer = _mock_generate_answer(query, retrieved)
            sp.set("answer_chars", len(answer))

        tr.set_output(answer=answer, citations=[d.id for d in retrieved[:2]])

    return answer
