from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .metrics import aggregate_quality, latency_summary_ms, span_latencies


def _read_traces(traces_dir: str) -> List[Dict[str, Any]]:
    p = Path(traces_dir)
    traces: List[Dict[str, Any]] = []
    if not p.exists():
        return traces
    for f in sorted(p.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                # skip broken line; report will highlight via validate command
                continue
    return traces


def generate_report_html(traces_dir: str, out_path: str) -> Path:
    traces = _read_traces(traces_dir)
    retrieve_lat = span_latencies(traces, "retrieve")
    rerank_lat = span_latencies(traces, "rerank")
    gen_lat = span_latencies(traces, "generate")

    sums = {
        "runs": len(traces),
        "retrieve": latency_summary_ms(retrieve_lat),
        "rerank": latency_summary_ms(rerank_lat),
        "generate": latency_summary_ms(gen_lat),
        "quality_k5": aggregate_quality(traces, k=5),
    }

    # "slow runs" heuristic
    slow = []
    for t in traces:
        total = (t.get("metrics", {}) or {}).get("latency_total_ms")
        try:
            total_i = int(total)
        except Exception:
            continue
        if total_i >= 2000:
            slow.append((t.get("run_id", "?"), total_i, (t.get("input", {}) or {}).get("query", "")))

    # retrieval misses
    misses = []
    for t in traces:
        gold = (t.get("input", {}) or {}).get("meta", {}).get("gold_doc_ids")
        if not isinstance(gold, list) or not gold:
            continue
        retrieved = None
        for s in t.get("spans", []):
            if s.get("name") == "retrieve":
                retrieved = s.get("attrs", {}).get("retrieved_ids", [])
                break
        if isinstance(retrieved, list):
            if not any(str(x) in set(map(str, gold)) for x in retrieved[:5]):
                misses.append((t.get("run_id","?"), (t.get("input", {}) or {}).get("query","")))

    # HTML
    def fmt_summary(label: str, d: Dict[str, Any]) -> str:
        return f"""<div class='card'>
  <div class='h'>{html.escape(label)}</div>
  <div class='kv'>count <b>{int(d.get('count',0))}</b></div>
  <div class='kv'>p50 <b>{d.get('p50')}</b> ms</div>
  <div class='kv'>p95 <b>{d.get('p95')}</b> ms</div>
  <div class='kv'>p99 <b>{d.get('p99')}</b> ms</div>
  <div class='kv'>avg <b>{d.get('avg')}</b> ms</div>
</div>"""

    q = sums["quality_k5"]
    quality_html = f"""<div class='card'>
  <div class='h'>Quality (labeled runs)</div>
  <div class='kv'>hit@5 <b>{q.get('hit_at_k')}</b></div>
  <div class='kv'>MRR <b>{q.get('mrr')}</b></div>
  <div class='kv'>answer_contains <b>{q.get('answer_contains')}</b></div>
  <div class='kv'>labeled <b>{int(q.get('labeled_runs',0))}</b></div>
</div>"""

    slow_rows = "".join(
        f"<tr><td>{html.escape(rid)}</td><td>{tot}</td><td>{html.escape(q[:120])}</td></tr>"
        for rid, tot, q in sorted(slow, key=lambda x: -x[1])[:50]
    )
    miss_rows = "".join(
        f"<tr><td>{html.escape(rid)}</td><td>{html.escape(q[:160])}</td></tr>"
        for rid, q in misses[:50]
    )

    out = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>rag-observatory report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
  .card {{ border: 1px solid #ddd; border-radius: 14px; padding: 12px 14px; box-shadow: 0 1px 2px rgba(0,0,0,.05); }}
  .h {{ font-weight: 700; margin-bottom: 8px; }}
  .kv {{ color: #222; margin: 3px 0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border-bottom: 1px solid #eee; padding: 8px; text-align: left; vertical-align: top; }}
  th {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: .04em; }}
  .muted {{ color: #666; font-size: 12px; }}
  code {{ background: #f6f6f6; padding: 2px 6px; border-radius: 8px; }}
</style>
</head>
<body>
<h1>rag-observatory report</h1>
<div class="muted">Traces: <code>{html.escape(traces_dir)}</code> • Runs: <b>{sums['runs']}</b></div>

<h2>Latency (ms)</h2>
<div class="grid">
{fmt_summary('retrieve', sums['retrieve'])}
{fmt_summary('rerank', sums['rerank'])}
{fmt_summary('generate', sums['generate'])}
{quality_html}
</div>

<h2>Slow runs (≥ 2000ms total)</h2>
<table>
  <thead><tr><th>run_id</th><th>total_ms</th><th>query</th></tr></thead>
  <tbody>{slow_rows or '<tr><td colspan="3" class="muted">none</td></tr>'}</tbody>
</table>

<h2>Retrieval misses (gold present, top‑5 missed)</h2>
<table>
  <thead><tr><th>run_id</th><th>query</th></tr></thead>
  <tbody>{miss_rows or '<tr><td colspan="2" class="muted">none</td></tr>'}</tbody>
</table>

<h2>How to read this</h2>
<ul>
  <li>If <b>retrieve p95</b> is high: optimize indexing, caching, or reduce top‑k.</li>
  <li>If <b>hit@5</b> is low: fix chunking, embeddings, or query rewrite.</li>
  <li>If <b>generate p95</b> is high: shorten prompts, stream, or switch model.</li>
</ul>

</body>
</html>"""

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(out, encoding="utf-8")
    return outp
