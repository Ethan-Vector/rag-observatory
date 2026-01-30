from rag_observatory.types import Document
from rag_observatory.chunking import chunk_document


def test_chunk_document_basic():
    doc = Document(doc_id="x.md", source_path="x.md", text="a" * 2000)
    chunks = chunk_document(doc, max_chars=900, overlap_chars=100, min_chars=120)
    assert len(chunks) >= 2
    assert chunks[0].chunk_id == "doc:x.md#chunk:0"
