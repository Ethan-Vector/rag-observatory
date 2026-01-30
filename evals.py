from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .pipeline import RagPipeline


@dataclass
class EvalResult:
    total: int
    hit_at_k: float
    recall_at_k: float
    no_answer_accuracy: float


def run_evals(pipeline: RagPipeline, golden_path: str) -> tuple[EvalResult, list[dict[str, Any]]]:
    cases = []
    with open(golden_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))

    total = len(cases)
    hits = 0
    recall_sum = 0.0
    no_answer_correct = 0
    rows = []

    for c in cases:
        out = pipeline.query(route=c.get("route", "default"), query=c["query"], top_k=None)
        citations = set(out["citations"])
        must = set(c.get("must_cite", []))

        hit = bool(must & citations) if must else (out["no_answer"] is True)
        hits += 1 if hit else 0

        recall = 1.0 if must.issubset(citations) and must else (1.0 if (not must and out["no_answer"]) else 0.0)
        recall_sum += recall

        should_answer = bool(c.get("should_answer", True))
        # if should_answer is False, we expect no_answer True
        na_ok = (out["no_answer"] is False) if should_answer else (out["no_answer"] is True)
        no_answer_correct += 1 if na_ok else 0

        rows.append(
            {
                "id": c.get("id"),
                "query": c["query"],
                "expected_must_cite": list(must),
                "got_citations": list(citations),
                "no_answer": out["no_answer"],
                "confidence": out["confidence"],
                "trace_id": out["trace_id"],
                "hit": hit,
                "recall": recall,
                "no_answer_ok": na_ok,
            }
        )

    res = EvalResult(
        total=total,
        hit_at_k=hits / max(1, total),
        recall_at_k=recall_sum / max(1, total),
        no_answer_accuracy=no_answer_correct / max(1, total),
    )
    return res, rows
