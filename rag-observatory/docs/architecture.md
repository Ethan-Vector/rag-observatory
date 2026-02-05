# Architecture

`rag-observatory` is deliberately simple:

- **Tracer**: manages a single `Trace` (one user request)
- **Span**: timed sub-operations (`retrieve`, `rerank`, `generate`)
- **Writer**: appends traces to JSONL
- **Metrics**: pure functions operating on parsed traces
- **Report**: creates a single-file HTML for quick review

## Why JSONL?

- append-only, rotation-friendly
- easy to stream / tail
- works with `jq`, `grep`, any log shipper
