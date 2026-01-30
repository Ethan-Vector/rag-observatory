from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class TraceBundle:
    trace_id: str
    ts_ms: int
    config_version: str
    route: str
    query: str
    rewrite: str
    top_k: int
    retrieval: list[dict[str, Any]]
    rerank: list[dict[str, Any]]
    decision: dict[str, Any]


class Tracer:
    def __init__(self, enabled: bool, traces_dir: str):
        self.enabled = enabled
        self.traces_dir = traces_dir

    def emit(self, bundle: TraceBundle) -> None:
        if not self.enabled:
            return
        os.makedirs(self.traces_dir, exist_ok=True)
        path = os.path.join(self.traces_dir, f"{bundle.trace_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(bundle.__dict__, f, ensure_ascii=False, indent=2)

    @staticmethod
    def new_trace_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def now_ms() -> int:
        return int(time.time() * 1000)
