from rag_observatory.embeddings import Embedder


def test_embedder_deterministic():
    e = Embedder(dim=64)
    v1 = e.embed("hello world")
    v2 = e.embed("hello world")
    assert v1 == v2
    assert len(v1) == 64
