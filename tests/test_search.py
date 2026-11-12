import pytest

from search import bm25_search, build_dense_index, dense_search, hybrid_search, load, rrf


def chunk(id, heading, text):
    return {"id": id, "source": id.split("#")[0], "heading": heading, "text": text}


CHUNKS = [
    chunk("a.md#0", "KubePodCrashLooping > Meaning", "Pod is restarting again and again."),
    chunk("b.md#0", "NodeFilesystemAlmostOutOfSpace > Meaning", "The disk on the node is nearly full."),
    chunk("c.md#0", "etcdNoLeader > Impact", "The cluster cannot accept writes."),
    chunk("d.md#0", "AlertmanagerFailedReload > Mitigation", "Check the configuration file for errors."),
    chunk("e.md#0", "NodeClockSkewDetected > Meaning", "Time on the node differs from the reference."),
]


def test_word_from_the_text_finds_its_chunk():
    results = bm25_search(CHUNKS, "disk full")
    assert results[0]["id"] == "b.md#0"


def test_alert_name_in_the_heading_finds_its_chunk():
    results = bm25_search(CHUNKS, "what does etcdNoLeader mean")
    assert results[0]["id"] == "c.md#0"


def test_returns_at_most_k_chunks():
    results = bm25_search(CHUNKS, "the node", k=2)
    assert len(results) == 2


def test_query_with_no_matching_word_returns_nothing():
    assert bm25_search(CHUNKS, "kafka rebalancing") == []


def test_dense_finds_a_chunk_that_shares_no_keyword_with_the_question():
    question = "my container keeps dying"
    assert bm25_search(CHUNKS, question) == []
    index = build_dense_index(CHUNKS, path=None)
    assert dense_search(index, question)[0]["id"] == "a.md#0"


def test_dense_returns_the_chunk_exactly_as_it_was_stored():
    index = build_dense_index(CHUNKS, path=None)
    assert dense_search(index, "etcd has lost its leader", k=1) == [CHUNKS[2]]


def test_rebuilding_the_index_forgets_chunks_that_were_removed():
    build_dense_index(CHUNKS, path=None)
    index = build_dense_index(CHUNKS[:2], path=None)
    assert len(dense_search(index, "node", k=5)) == 2


def ids(chunks):
    return [c["id"] for c in chunks]


A, B, C, D = ({"id": letter} for letter in "abcd")


def test_rrf_puts_a_chunk_found_by_both_searches_above_one_found_by_a_single_search():
    assert ids(rrf([[A, B], [C, B]])) == ["b", "a", "c"]


def test_rrf_lists_each_chunk_once():
    assert ids(rrf([[A, B], [A, B]])) == ["a", "b"]


def test_rrf_returns_at_most_k_chunks():
    assert len(rrf([[A, B], [C, D]], k=3)) == 3


def test_hybrid_finds_an_exact_alert_name_and_a_paraphrase():
    index = build_dense_index(CHUNKS, path=None)
    assert hybrid_search(CHUNKS, index, "etcdNoLeader")[0]["id"] == "c.md#0"
    assert hybrid_search(CHUNKS, index, "my container keeps dying")[0]["id"] == "a.md#0"


def test_load_says_what_to_run_when_the_index_has_not_been_built(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="make index"):
        load()
