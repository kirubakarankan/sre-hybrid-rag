from search import bm25_search


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
