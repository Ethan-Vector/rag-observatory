from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citations: list[str]
    confidence: float
    no_answer: bool


def grounded_answer(query: str, passages: list[dict], max_context_chars: int, threshold: float) -> AnswerResult:
    """
    Answer semplice e grounded:
    - prende top passages (post-rerank)
    - costruisce un contesto compatto
    - confidence = max(rerank_score or score)
    - se confidence < threshold -> no-answer
    """
    if not passages:
        return AnswerResult(
            answer="I don't have enough evidence to answer from the indexed knowledge.",
            citations=[],
            confidence=0.0,
            no_answer=True,
        )

    best = passages[0]
    conf = float(best.get("rerank_score", best.get("score", 0.0)))

    if conf < threshold:
        return AnswerResult(
            answer="I don't have enough evidence to answer from the indexed knowledge.",
            citations=[],
            confidence=conf,
            no_answer=True,
        )

    # build compact context
    ctx = []
    used = 0
    cites = []
    for p in passages:
        t = p["text"].strip()
        if not t:
            continue
        if used + len(t) > max_context_chars:
            break
        ctx.append(t)
        used += len(t)
        cites.append(p["chunk_id"])

    # grounded “answer”: conservative summarization
    answer = (
        "Based on the indexed documents, here is the relevant guidance:\n\n"
        + "\n\n".join(ctx)
        + "\n\n(Answer grounded in retrieved passages.)"
    )
    return AnswerResult(answer=answer, citations=cites, confidence=conf, no_answer=False)
