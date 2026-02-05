from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .demo_pipeline import run_demo
from .report import generate_report_html
from .schema import validate_trace_dict


def _read_all_traces(traces_dir: str) -> List[Dict[str, Any]]:
    p = Path(traces_dir)
    traces: List[Dict[str, Any]] = []
    if not p.exists():
        return traces
    for f in sorted(p.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                traces.append({"_broken_line": line, "schema_version": -1})
    return traces


def cmd_demo(args: argparse.Namespace) -> int:
    qs = [
        "What is RAG?",
        "Why does chunking matter?",
        "How do I keep a RAG system honest?",
        "How do I think about latency budgets?",
    ]
    # Add some labels so report shows quality metrics
    labels = {
        qs[0]: {"gold_doc_ids": ["000_rag_basics"], "expected_answer_contains": ["retrieval"]},
        qs[1]: {"gold_doc_ids": ["001_chunking"], "expected_answer_contains": ["chunk"]},
        qs[2]: {"gold_doc_ids": ["002_eval_loop"], "expected_answer_contains": ["eval"]},
        qs[3]: {"gold_doc_ids": ["003_latency_budget"], "expected_answer_contains": ["latency"]},
    }
    for q in qs[: args.n]:
        m = labels.get(q, {})
        run_demo(q, gold_doc_ids=m.get("gold_doc_ids"), expected_answer_contains=m.get("expected_answer_contains"))
    print(f"wrote demo traces to {os.getenv('RAGOBS_TRACE_DIR', 'workspace/traces')}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    out = generate_report_html(args.traces, args.out)
    print(f"report written: {out}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    traces = _read_all_traces(args.traces)
    bad = 0
    for t in traces:
        if "_broken_line" in t:
            bad += 1
            continue
        errs = validate_trace_dict(t)
        if errs:
            bad += 1
    if bad:
        print(f"validation failed: {bad} problematic runs/lines")
        return 2
    print("validation OK")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    # Offline eval harness using the demo pipeline (replace with your pipeline in real use).
    dataset_path = Path(args.dataset)
    rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    results = []
    for r in rows:
        q = r["query"]
        answer = run_demo(
            q,
            gold_doc_ids=r.get("gold_doc_ids"),
            expected_answer_contains=r.get("expected_answer_contains"),
        )
        results.append({"query": q, "answer": answer})

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps({"runs": len(results), "results": results}, indent=2), encoding="utf-8")
    print(f"eval output written: {outp}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ragobs", description="Offline-first RAG observability toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="Run demo pipeline and write traces")
    d.add_argument("-n", type=int, default=4, help="number of demo queries")
    d.set_defaults(func=cmd_demo)

    r = sub.add_parser("report", help="Generate single-file HTML report from traces")
    r.add_argument("--traces", default=os.getenv("RAGOBS_TRACE_DIR", "workspace/traces"))
    r.add_argument("--out", default="workspace/report.html")
    r.set_defaults(func=cmd_report)

    v = sub.add_parser("validate", help="Validate JSONL traces against schema (best-effort)")
    v.add_argument("--traces", default=os.getenv("RAGOBS_TRACE_DIR", "workspace/traces"))
    v.set_defaults(func=cmd_validate)

    e = sub.add_parser("eval", help="Run offline smoke eval dataset (demo pipeline)")
    e.add_argument("--dataset", default="evals/datasets/smoke.jsonl")
    e.add_argument("--out", default="workspace/evals.json")
    e.set_defaults(func=cmd_eval)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
