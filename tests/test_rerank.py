from rerank import rerank
from tests.test_search import CHUNKS


def test_rerank_moves_the_relevant_chunk_from_last_to_first():
    assert CHUNKS[-1]["id"] == "e.md#0"
    results = rerank("the time on my server is wrong", CHUNKS)
    assert results[0]["id"] == "e.md#0"


def test_rerank_returns_at_most_k_chunks():
    assert len(rerank("node", CHUNKS, k=2)) == 2
