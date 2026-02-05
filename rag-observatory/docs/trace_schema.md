# Trace schema (v1)

Top-level:

- `schema_version`: int (currently 1)
- `run_id`: str
- `ts`: ISO timestamp (UTC)
- `input`: { `query`: str, `meta`: dict }
- `spans`: list[Span]
- `output`: { `answer`: str, `citations`: list[str] }
- `metrics`: dict

Span:

- `name`: str (`retrieve` | `rerank` | `generate` | custom)
- `start_ms`, `end_ms`: int (ms since trace start)
- `attrs`: dict (free-form, but keep it JSON-serializable)

## Conventions (so metrics work)

If you want retrieval metrics, set:
- `retrieve.attrs.retrieved_ids`: list[str] (doc ids)
- `input.meta.gold_doc_ids`: list[str] (optional, for offline evals)

For generation heuristics:
- `output.answer` (required)
- `input.meta.expected_answer_contains`: list[str] (optional, offline eval)
