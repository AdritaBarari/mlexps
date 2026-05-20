from functools import lru_cache

from sentence_transformers import CrossEncoder

from config import RAGConfig


@lru_cache(maxsize=4)
def _get_cross_encoder(model_name: str) -> CrossEncoder:
    return CrossEncoder(model_name)


def rerank(query: str, chunks: list[dict], config: RAGConfig) -> list[dict]:
    if not chunks:
        return []

    model = _get_cross_encoder(config.rerank_model)
    pairs = [(query, c["text"]) for c in chunks]
    scores = model.predict(pairs).tolist()

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = score

    ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[: config.rerank_top_n]
