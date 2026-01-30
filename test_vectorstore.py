from rag_observatory.vectorstore import VectorStore
from rag_observatory.types import Chunk


def test_vectorstore_insert_and_search(tmp_path):
    db = tmp_path / "t.sqlite"
    vs = VectorStore(str(db))
    vs.init()
    c = Chunk(chunk_id="doc:a#chunk:0", doc_id="a", idx=0, text="hello password reset", meta={})
    vs.upsert_chunks([c], {"doc:a#chunk:0": [1.0, 0.0]})
    res = vs.search([1.0, 0.0], top_k=1)
    assert res[0]["chunk_id"] == "doc:a#chunk:0"
