import json
from pathlib import Path

from rag_observatory.tracing import trace_run


def test_trace_run_writes_jsonl(tmp_path: Path):
    td = tmp_path / "traces"
    with trace_run("q", trace_dir=str(td)) as tr:
        with tr.span("retrieve") as sp:
            sp.set("retrieved_ids", ["d1"])
        tr.set_output(answer="a")
    files = list(td.glob("*.jsonl"))
    assert files, "expected a jsonl file"
    line = files[0].read_text(encoding="utf-8").splitlines()[0]
    obj = json.loads(line)
    assert obj["input"]["query"] == "q"
