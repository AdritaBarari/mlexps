from sentence_transformers import CrossEncoder

from config import RAGConfig


def rerank(query: str, chunks: list[dict], config: RAGConfig) -> list[dict]:
    if not chunks:
        return []

    model = CrossEncoder(config.rerank_model)
    pairs = [(query, c["text"]) for c in chunks]
    scores = model.predict(pairs).tolist()

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = score

    ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[: config.rerank_top_n]
