from rag_observatory.schema import SCHEMA_VERSION, validate_trace_dict


def test_validate_trace_happy_path():
    t = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "abc",
        "ts": "2026-01-01T00:00:00Z",
        "input": {"query": "q", "meta": {}},
        "spans": [{"name": "retrieve", "start_ms": 0, "end_ms": 10, "attrs": {"retrieved_ids": ["d1"]}}],
        "output": {"answer": "a", "citations": []},
        "metrics": {"latency_total_ms": 10},
    }
    assert validate_trace_dict(t) == []
