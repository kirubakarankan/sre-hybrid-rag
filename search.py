"""Find the chunks that best match a question."""
import json
import re
import sys

from rank_bm25 import BM25Okapi


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_search(chunks, query, k=5):
    # shortcut: the index is rebuilt on every call, which takes milliseconds for a few
    # hundred chunks. Build it once and reuse it when the corpus reaches tens of thousands.
    index = BM25Okapi([words(c["heading"] + " " + c["text"]) for c in chunks])
    scores = index.get_scores(words(query))
    best_first = sorted(zip(scores, chunks), key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in best_first[:k] if score > 0]


if __name__ == "__main__":
    chunks = [json.loads(line) for line in open("chunks.jsonl")]
    for chunk in bm25_search(chunks, sys.argv[1]):
        print(f"{chunk['id']:55} {chunk['heading']}")
