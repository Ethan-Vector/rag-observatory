from __future__ import annotations

def lexical_overlap_score(query: str, text: str) -> float:
    q = set(_tokens(query))
    t = set(_tokens(text))
    if not q:
        return 0.0
    inter = len(q & t)
    return inter / max(1, len(q))


def rerank_lexical(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    out = []
    for c in candidates:
        s2 = lexical_overlap_score(query, c["text"])
        c2 = dict(c)
        c2["rerank_score"] = float(s2)
        out.append(c2)
    out.sort(key=lambda x: (x["rerank_score"], x["score"]), reverse=True)
    return out[:top_k]


def _tokens(text: str) -> list[str]:
    cur = []
    out = []
    for ch in text.lower():
        if ch.isalnum():
            cur.append(ch)
        else:
            if cur:
                out.append("".join(cur))
                cur = []
    if cur:
        out.append("".join(cur))
    return out
