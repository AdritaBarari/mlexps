import chromadb
from sentence_transformers import SentenceTransformer

from config import RAGConfig


def retrieve(query: str, config: RAGConfig) -> list[dict]:
    client = chromadb.PersistentClient(path=str(config.persist_dir))
    collection = client.get_or_create_collection(config.collection_name)

    embedder = SentenceTransformer(config.embed_model)
    query_embedding = embedder.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(config.retrieval_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "filename": meta["filename"],
            "page": meta["page"],
            "score": 1 - dist,  # cosine similarity from distance
        })
    return chunks
