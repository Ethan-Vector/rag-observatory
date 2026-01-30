from __future__ import annotations

from .types import Chunk, Document


def chunk_document(doc: Document, max_chars: int, overlap_chars: int, min_chars: int) -> list[Chunk]:
    text = doc.text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    n = len(text)

    while start < n:
        end = min(n, start + max_chars)
        chunk_text = text[start:end].strip()

        if len(chunk_text) >= min_chars or (idx == 0 and end == n):
            chunk_id = f"doc:{doc.doc_id}#chunk:{idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc.doc_id,
                    idx=idx,
                    text=chunk_text,
                    meta={"source_path": doc.source_path, "start": start, "end": end},
                )
            )
            idx += 1

        if end == n:
            break

        # overlap
        start = max(0, end - overlap_chars)

    return chunks
