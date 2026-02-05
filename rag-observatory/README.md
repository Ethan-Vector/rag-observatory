# rag-observatory

A small, **offline-first RAG observability kit**: trace your retrieval → (optional) rerank → generation steps, compute repeatable metrics, and produce a single-file HTML report you can ship to teammates.

This repo is intentionally minimal and vendor-neutral:
- **No SaaS**, no hidden telemetry
- **JSONL traces** (easy to diff, grep, archive)
- **CLI-first** workflows (CI-friendly)
- **Toy demo pipeline** included so you can validate end‑to‑end without keys

> If you already have a RAG pipeline, you mainly want `rag_observatory.tracing` + `ragobs report`.

---

## What you get

- Tracing primitives: `Trace`, `Span`, `Tracer`
- Standard span names: `retrieve`, `rerank`, `generate`
- Metrics: latency percentiles, hit@k / MRR, answer checks (offline heuristics)
- HTML report generator (single file, no server required)
- Evals harness + smoke dataset
- GitHub Actions CI, Docker, tests

---

## Quickstart (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ragobs demo
ragobs report --traces workspace/traces --out workspace/report.html
```

Open `workspace/report.html`.

---

## CLI overview

```bash
ragobs demo                         # generate a few demo traces
ragobs report --traces DIR --out FILE
ragobs eval   --dataset evals/datasets/smoke.jsonl --out workspace/evals.json
ragobs validate --traces DIR         # schema checks + basic sanity rules
```

---

## Trace format (high level)

Each line is one run (JSONL):

- `run_id`, `ts`, `input.query`
- `spans[]` with `name`, `start_ms`, `end_ms`, `attrs`
- `output.answer` (+ optional `output.citations`)
- `metrics` (tokens/cost placeholders, latency totals, etc.)

See `docs/trace_schema.md`.

---

## How to integrate with your pipeline

Minimal pattern:

```python
from rag_observatory.tracing import trace_run

with trace_run(query="...") as tr:
    with tr.span("retrieve", top_k=5) as sp:
        docs = my_retriever(query)
        sp.set("retrieved_ids", [d.id for d in docs])

    with tr.span("generate") as sp:
        answer = my_llm(prompt)
        sp.set("prompt_chars", len(prompt))

    tr.set_output(answer=answer, citations=[...])
```

---

## License

MIT. See `LICENSE`.
