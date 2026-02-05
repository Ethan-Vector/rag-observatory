# KR (Keep-Repo) Instructions — rag-observatory

This repo is designed to be dropped into any RAG codebase and used in three modes:

1) **Tracing only**: write JSONL traces you can archive.
2) **Tracing + reporting**: generate a single-file HTML report.
3) **Tracing + evals**: run repeatable smoke evals in CI.

## Recommended workflow

- During development: run `ragobs demo` or instrument your pipeline and generate `ragobs report`.
- Before shipping: add a smoke dataset and run `ragobs eval` in CI.
- In production: log traces to a directory per env, rotate daily, and sample.

## What to edit first

- `configs/config.example.yaml` → copy to `configs/config.yaml` and tune:
  - trace output directory
  - default budgets/limits
  - report thresholds (latency, hit@k)
- Replace the demo pipeline in `src/rag_observatory/demo_pipeline.py` with your real pipeline integration.

## Common pitfalls

- Traces missing `retrieved_ids` → you can’t compute hit@k.
- Not recording `latency_ms` → you can’t do SLO-like checks.
- Mixing schema versions → keep `schema_version` stable and bump intentionally.

## CI suggestion

Add a nightly workflow:
- run smoke evals
- upload report artifact
