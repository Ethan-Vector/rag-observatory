# Reporting

`ragobs report` reads JSONL traces and emits a single HTML file.

Included sections:
- Summary stats (runs, error rate)
- Latency percentiles per span
- Retrieval quality (hit@k, MRR) if gold labels exist
- “Slow runs” and “missed retrieval” tables

This is not a dashboard replacement; it's a **fast inspection artifact** you can attach to PRs.
