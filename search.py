"""Find the chunks that best match a question."""
import json
import re
import sys
from functools import cache

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_search(chunks, query, k=5):
    # shortcut: the index is rebuilt on every call, which takes milliseconds for a few
    # hundred chunks. Build it once and reuse it when the corpus reaches tens of thousands.
    index = BM25Okapi([words(c["heading"] + " " + c["text"]) for c in chunks])
    scores = index.get_scores(words(query))
    best_first = sorted(zip(scores, chunks), key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in best_first[:k] if score > 0]


@cache  # loading the model takes seconds, so do it once and only when it is needed
def model():
    return SentenceTransformer("BAAI/bge-small-en-v1.5")


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
        for id, metadata, text in zip(found["ids"][0], found["metadatas"][0], found["documents"][0])
    ]


def show(title, chunks):
    print(title)
    for chunk in chunks:
        print(f"  {chunk['id']:53} {chunk['heading']}")


if __name__ == "__main__":
    chunks = [json.loads(line) for line in open("chunks.jsonl")]
    if sys.argv[1] == "index":
        build_dense_index(chunks)
        print(f"indexed {len(chunks)} chunks -> chroma/")
    else:
        show("BM25 (keywords)", bm25_search(chunks, sys.argv[1]))
        show("Dense (meaning)", dense_search(chromadb.PersistentClient("chroma").get_collection("chunks"), sys.argv[1]))
