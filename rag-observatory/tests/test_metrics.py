from rag_observatory.metrics import hit_at_k, reciprocal_rank, answer_contains_checks


def test_quality_metrics():
    t = {
        "input": {"meta": {"gold_doc_ids": ["d2"], "expected_answer_contains": ["hello"]}},
        "spans": [{"name": "retrieve", "attrs": {"retrieved_ids": ["d1", "d2"]}, "start_ms": 0, "end_ms": 1}],
        "output": {"answer": "Hello world"},
        "metrics": {},
    }
    assert hit_at_k(t, 1) == 0.0
    assert hit_at_k(t, 2) == 1.0
    assert reciprocal_rank(t) == 0.5
    assert answer_contains_checks(t) == 1.0
