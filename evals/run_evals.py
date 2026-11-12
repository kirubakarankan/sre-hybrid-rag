"""Measure how often each search method finds the right runbook. Run: make eval"""
import json
from pathlib import Path

K = 5


def reciprocal_rank(results, source):
    for rank, chunk in enumerate(results, start=1):
        if chunk["source"] == source:
            return 1 / rank
    return 0


if __name__ == "__main__":
    import chromadb

    from rerank import rerank
    from search import bm25_search, dense_search, hybrid_search

    chunks = [json.loads(line) for line in open("chunks.jsonl")]
    index = chromadb.PersistentClient("chroma").get_collection("chunks")
    questions = [json.loads(line) for line in open(Path(__file__).parent / "questions.jsonl")]

    methods = {
        "BM25": lambda q: bm25_search(chunks, q, K),
        "Dense": lambda q: dense_search(index, q, K),
        "Hybrid": lambda q: hybrid_search(chunks, index, q, K),
        "Hybrid + rerank": lambda q: rerank(q, hybrid_search(chunks, index, q, k=20), K),
    }
    kinds = sorted({q["kind"] for q in questions})

    print(f"| Method | recall@{K} | MRR | " + " | ".join(f"recall@{K} ({kind})" for kind in kinds) + " |")
    print("|---|---|---|" + "---|" * len(kinds))
    for name, search in methods.items():
        scores = [(q["kind"], reciprocal_rank(search(q["question"]), q["source"])) for q in questions]
        found = [rr > 0 for _, rr in scores]
        by_kind = [
            sum(rr > 0 for kind, rr in scores if kind == wanted) / sum(kind == wanted for kind, _ in scores)
            for wanted in kinds
        ]
        cells = [sum(found) / len(found), sum(rr for _, rr in scores) / len(scores), *by_kind]
        print(f"| {name} | " + " | ".join(f"{value:.2f}" for value in cells) + " |")
