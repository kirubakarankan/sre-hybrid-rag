"""Find the chunks that best match a question."""
import json
import re
import sys
from functools import cache
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from rerank import rerank

# Question words are rare in terse runbooks, so without this they outscore the alert name.
# Only question words: a longer list (the, is, of ...) scored worse on the evaluation questions.
STOP_WORDS = set("can do does how i me my should we what when where which who why you".split())


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_search(chunks, query, k=5):
    # shortcut: the index is rebuilt on every call, which takes milliseconds for a few
    # hundred chunks. Build it once and reuse it when the corpus reaches tens of thousands.
    index = BM25Okapi([words(c["heading"] + " " + c["text"]) for c in chunks])
    scores = index.get_scores([w for w in words(query) if w not in STOP_WORDS])
    best_first = sorted(zip(scores, chunks, strict=True), key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in best_first[:k] if score > 0]


@cache  # loading the model takes seconds, so do it once and only when it is needed
def model():
    # The revision pins the exact model files, so results do not change if the model is updated.
    return SentenceTransformer("BAAI/bge-small-en-v1.5", revision="5c38ec7c405ec4b44b94cc5a9bb96e735b38267a")


def embed(texts):
    # Vectors are scaled to length 1, so Chroma's default distance ranks like cosine similarity.
    return model().encode(texts, normalize_embeddings=True).tolist()


def build_dense_index(chunks, path="chroma"):
    client = chromadb.PersistentClient(path) if path else chromadb.EphemeralClient()
    # Start from empty so chunks that were removed from the corpus do not linger.
    client.get_or_create_collection("chunks")
    client.delete_collection("chunks")
    index = client.create_collection("chunks")
    index.add(
        ids=[c["id"] for c in chunks],
        embeddings=embed([c["heading"] + "\n" + c["text"] for c in chunks]),
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "heading": c["heading"]} for c in chunks],
    )
    return index


def dense_search(index, query, k=5):
    found = index.query(query_embeddings=embed([query]), n_results=k)
    return [
        {"id": id, **metadata, "text": text}
        for id, metadata, text in zip(found["ids"][0], found["metadatas"][0], found["documents"][0], strict=True)
    ]


def rrf(ranked_lists, k=5):
    """Reciprocal Rank Fusion: merge ranked lists using only each chunk's position."""
    score, chunk_by_id = {}, {}
    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked, start=1):
            # 60 is the constant from the original RRF paper; it stops rank 1 from dominating.
            score[chunk["id"]] = score.get(chunk["id"], 0) + 1 / (60 + rank)
            chunk_by_id[chunk["id"]] = chunk
    best_first = sorted(score, key=score.get, reverse=True)
    return [chunk_by_id[id] for id in best_first[:k]]


def hybrid_search(chunks, index, query, k=5):
    # Each search contributes its top 20, so a chunk ranked low by one can still be rescued.
    return rrf([bm25_search(chunks, query, k=20), dense_search(index, query, k=20)], k)


def load():
    chunks_file, built = Path("chunks.jsonl"), Path("chroma/.indexed")
    if not (chunks_file.exists() and built.exists()) or chunks_file.stat().st_mtime > built.stat().st_mtime:
        sys.exit("The index is missing, unfinished or older than chunks.jsonl. Run: make index")
    with open("chunks.jsonl") as f:
        chunks = [json.loads(line) for line in f]
    return chunks, chromadb.PersistentClient("chroma").get_collection("chunks")


def show(title, chunks):
    print(title)
    for chunk in chunks:
        print(f"  {chunk['id']:53} {chunk['heading']}")


if __name__ == "__main__":
    if sys.argv[1] == "index":
        with open("chunks.jsonl") as f:
            chunks = [json.loads(line) for line in f]
        build_dense_index(chunks)
        Path("chroma/.indexed").touch()  # written last, so an interrupted build leaves no marker
        print(f"indexed {len(chunks)} chunks -> chroma/")
    else:
        chunks, index = load()
        show("BM25 (keywords)", bm25_search(chunks, sys.argv[1]))
        show("Dense (meaning)", dense_search(index, sys.argv[1]))
        show("Hybrid (both, fused)", hybrid_search(chunks, index, sys.argv[1]))
        show("Hybrid + rerank", rerank(sys.argv[1], hybrid_search(chunks, index, sys.argv[1], k=20)))
