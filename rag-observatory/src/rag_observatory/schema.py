from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = 1


@dataclass
class Span:
    name: str
    start_ms: int
    end_ms: int
    attrs: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)


@dataclass
class Trace:
    schema_version: int
    run_id: str
    ts: str
    input: Dict[str, Any]
    spans: List[Span]
    output: Dict[str, Any]
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "ts": self.ts,
            "input": self.input,
            "spans": [
                {"name": s.name, "start_ms": s.start_ms, "end_ms": s.end_ms, "attrs": s.attrs}
                for s in self.spans
            ],
            "output": self.output,
            "metrics": self.metrics,
        }


def validate_trace_dict(d: Dict[str, Any]) -> List[str]:
    """Return a list of validation errors (empty if OK)."""
    errs: List[str] = []
    if not isinstance(d, dict):
        return ["trace is not a dict"]

    if d.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version must be {SCHEMA_VERSION}")

    for key in ["run_id", "ts", "input", "spans", "output", "metrics"]:
        if key not in d:
            errs.append(f"missing key: {key}")

    if "spans" in d and not isinstance(d["spans"], list):
        errs.append("spans must be a list")

    if "input" in d and not isinstance(d["input"], dict):
        errs.append("input must be a dict")

    if "output" in d and not isinstance(d["output"], dict):
        errs.append("output must be a dict")

    # Span checks (best-effort)
    spans = d.get("spans", [])
    if isinstance(spans, list):
        for i, s in enumerate(spans):
            if not isinstance(s, dict):
                errs.append(f"span[{i}] is not a dict")
                continue
            for k in ["name", "start_ms", "end_ms", "attrs"]:
                if k not in s:
                    errs.append(f"span[{i}] missing {k}")
            if "attrs" in s and not isinstance(s["attrs"], dict):
                errs.append(f"span[{i}].attrs must be a dict")

    return errs
