from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from rag_observatory.demo_pipeline import run_demo


def run(dataset_path: str) -> Dict[str, Any]:
    p = Path(dataset_path)
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    out: List[Dict[str, Any]] = []
    for r in rows:
        ans = run_demo(
            r["query"],
            gold_doc_ids=r.get("gold_doc_ids"),
            expected_answer_contains=r.get("expected_answer_contains"),
        )
        out.append({"query": r["query"], "answer": ans})
    return {"runs": len(out), "results": out}


def main() -> None:
    report = run("evals/datasets/smoke.jsonl")
    Path("workspace").mkdir(exist_ok=True)
    Path("workspace/evals.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote workspace/evals.json")


if __name__ == "__main__":
    main()
