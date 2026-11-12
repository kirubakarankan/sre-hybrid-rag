"""Re-order search results by reading the question and each chunk together."""
from functools import cache

from sentence_transformers import CrossEncoder


@cache  # loading the model takes seconds, so do it once and only when it is needed
def model():
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(query, chunks, k=5):
    scores = model().predict([(query, c["heading"] + "\n" + c["text"]) for c in chunks])
    best_first = sorted(zip(scores, chunks), key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in best_first[:k]]
