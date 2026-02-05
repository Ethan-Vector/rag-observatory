from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .schema import SCHEMA_VERSION, Span, Trace


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ms_since(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


@dataclass
class SpanHandle:
    _tracer: "Tracer"
    _name: str
    _start_ms: int
    _attrs: Dict[str, Any]

    def set(self, key: str, value: Any) -> None:
        self._attrs[key] = value

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            self._attrs[k] = v

    def end(self) -> None:
        end_ms = _ms_since(self._tracer._t0)
        self._tracer._spans.append(Span(name=self._name, start_ms=self._start_ms, end_ms=end_ms, attrs=self._attrs))

    def __enter__(self) -> "SpanHandle":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self._attrs["error"] = str(exc)
        self.end()


class Tracer:
    """In-memory trace builder for a single run."""

    def __init__(self, query: str, meta: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None) -> None:
        self.run_id = run_id or uuid.uuid4().hex
        self._t0 = time.perf_counter()
        self._input: Dict[str, Any] = {"query": query, "meta": meta or {}}
        self._spans: List[Span] = []
        self._output: Dict[str, Any] = {"answer": "", "citations": []}
        self._metrics: Dict[str, Any] = {}

    def span(self, name: str, **attrs: Any) -> SpanHandle:
        start_ms = _ms_since(self._t0)
        return SpanHandle(self, name, start_ms, dict(attrs))

    def set_input_meta(self, **meta: Any) -> None:
        self._input.setdefault("meta", {}).update(meta)

    def set_output(self, *, answer: str, citations: Optional[List[str]] = None, **extra: Any) -> None:
        self._output["answer"] = answer
        if citations is not None:
            self._output["citations"] = citations
        for k, v in extra.items():
            self._output[k] = v

    def set_metric(self, key: str, value: Any) -> None:
        self._metrics[key] = value

    def finalize(self) -> Trace:
        total_ms = _ms_since(self._t0)
        self._metrics.setdefault("latency_total_ms", total_ms)
        return Trace(
            schema_version=SCHEMA_VERSION,
            run_id=self.run_id,
            ts=_now_iso_utc(),
            input=self._input,
            spans=self._spans,
            output=self._output,
            metrics=self._metrics,
        )


def write_trace_jsonl(trace: Trace, trace_dir: str) -> Path:
    out_dir = Path(trace_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = out_dir / f"traces-{day}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
    return path


@contextmanager
def trace_run(
    query: str,
    *,
    meta: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    trace_dir: Optional[str] = None,
) -> Iterator[Tracer]:
    """Context manager that auto-writes the trace as JSONL on exit."""
    tracer = Tracer(query=query, meta=meta, run_id=run_id)
    try:
        yield tracer
    finally:
        td = trace_dir or os.getenv("RAGOBS_TRACE_DIR", "workspace/traces")
        trace = tracer.finalize()
        write_trace_jsonl(trace, td)
