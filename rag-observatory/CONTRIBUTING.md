# Contributing

- Keep runtime dependencies **zero** unless there's a strong reason.
- Add features as *optional extras* if they increase footprint.
- Every new metric should ship with:
  - a unit test
  - a doc note in `docs/`
  - a demo trace example (if useful)

## Dev setup

```bash
pip install -e ".[dev]"
ruff check .
pytest
```
