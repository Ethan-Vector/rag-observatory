from __future__ import annotations

import argparse
import json
import sys

from .config import load_config
from .pipeline import RagPipeline
from .evals import run_evals


def main() -> None:
    p = argparse.ArgumentParser(prog="ragobs")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="Ingest corpus into sqlite store")
    p_ing.add_argument("--config", required=True)

    p_q = sub.add_parser("query", help="Query the RAG pipeline (CLI)")
    p_q.add_argument("--config", required=True)
    p_q.add_argument("--route", default="default")
    p_q.add_argument("--q", required=True)
    p_q.add_argument("--top-k", type=int, default=None)

    p_e = sub.add_parser("eval", help="Run regression evals on golden set")
    p_e.add_argument("--config", required=True)
    p_e.add_argument("--golden", required=True)

    args = p.parse_args()

    cfg = load_config(args.config)
    pipe = RagPipeline.from_config(cfg)

    if args.cmd == "ingest":
        stats = pipe.ingest()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    if args.cmd == "query":
        out = pipe.query(route=args.route, query=args.q, top_k=args.top_k)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if args.cmd == "eval":
        res, rows = run_evals(pipe, args.golden)
        print(json.dumps(res.__dict__, ensure_ascii=False, indent=2))
        # print failing cases summary to stderr
        failed = [r for r in rows if not (r["hit"] and r["no_answer_ok"])]
        if failed:
            print(f"\nFailures: {len(failed)}/{res.total}", file=sys.stderr)
            for r in failed[:10]:
                print(f"- {r['id']}: hit={r['hit']} no_answer_ok={r['no_answer_ok']} trace={r['trace_id']}", file=sys.stderr)
        return


if __name__ == "__main__":
    main()
