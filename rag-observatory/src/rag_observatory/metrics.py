from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
import math
import statistics


def _percentile(xs: List[float], p: float) -> float:
    if not xs:
        return float("nan")
    xs_sorted = sorted(xs)
    k = (len(xs_sorted) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(xs_sorted[int(k)])
    d0 = xs_sorted[int(f)] * (c - k)
    d1 = xs_sorted[int(c)] * (k - f)
    return float(d0 + d1)


def span_latencies(traces: Iterable[Dict[str, Any]], span_name: str) -> List[int]:
    lats: List[int] = []
    for t in traces:
        for s in t.get("spans", []):
            if s.get("name") == span_name:
                lats.append(max(0, int(s.get("end_ms", 0)) - int(s.get("start_ms", 0))))
    return lats


def latency_summary_ms(latencies: List[int]) -> Dict[str, float]:
    if not latencies:
        return {"count": 0, "p50": float("nan"), "p95": float("nan"), "p99": float("nan"), "avg": float("nan")}
    xs = [float(x) for x in latencies]
    return {
        "count": float(len(xs)),
        "p50": _percentile(xs, 0.50),
        "p95": _percentile(xs, 0.95),
        "p99": _percentile(xs, 0.99),
        "avg": float(statistics.fmean(xs)),
    }


def retrieval_ids(trace: Dict[str, Any]) -> List[str]:
    for s in trace.get("spans", []):
        if s.get("name") == "retrieve":
            ids = s.get("attrs", {}).get("retrieved_ids")
            if isinstance(ids, list):
                return [str(x) for x in ids]
    return []


def gold_ids(trace: Dict[str, Any]) -> List[str]:
    meta = trace.get("input", {}).get("meta", {})
    ids = meta.get("gold_doc_ids")
    if isinstance(ids, list):
        return [str(x) for x in ids]
    return []


def hit_at_k(trace: Dict[str, Any], k: int) -> Optional[float]:
    gold = set(gold_ids(trace))
    if not gold:
        return None
    retrieved = retrieval_ids(trace)[:k]
    return 1.0 if any(r in gold for r in retrieved) else 0.0


def reciprocal_rank(trace: Dict[str, Any]) -> Optional[float]:
    gold = set(gold_ids(trace))
    if not gold:
        return None
    retrieved = retrieval_ids(trace)
    for i, r in enumerate(retrieved, start=1):
        if r in gold:
            return 1.0 / float(i)
    return 0.0


def answer_contains_checks(trace: Dict[str, Any]) -> Optional[float]:
    meta = trace.get("input", {}).get("meta", {})
    needles = meta.get("expected_answer_contains")
    if not isinstance(needles, list) or not needles:
        return None
    answer = (trace.get("output", {}) or {}).get("answer", "")
    if not isinstance(answer, str):
        return None
    a = answer.lower()
    ok = 0
    for n in needles:
        if isinstance(n, str) and n.lower() in a:
            ok += 1
    return float(ok) / float(len(needles))


def aggregate_quality(traces: Iterable[Dict[str, Any]], k: int = 5) -> Dict[str, float]:
    hits: List[float] = []
    mrrs: List[float] = []
    ans: List[float] = []
    for t in traces:
        h = hit_at_k(t, k)
        if h is not None:
            hits.append(h)
        r = reciprocal_rank(t)
        if r is not None:
            mrrs.append(r)
        a = answer_contains_checks(t)
        if a is not None:
            ans.append(a)

    def avg(xs: List[float]) -> float:
        return float(statistics.fmean(xs)) if xs else float("nan")

    return {
        "hit_at_k": avg(hits),
        "mrr": avg(mrrs),
        "answer_contains": avg(ans),
        "labeled_runs": float(max(len(hits), len(mrrs), len(ans))),
    }
