import os
from pathlib import Path

import chromadb
import fitz
from sentence_transformers import SentenceTransformer

from config import RAGConfig


def load_pdf(path: str) -> list[dict]:
    doc = fitz.open(path)
    filename = Path(path).name
    pages = []
    for page_num in range(len(doc)):
        text = doc[page_num].get_text().strip()
        if text:
            pages.append({"text": text, "page": page_num + 1, "filename": filename})
    doc.close()
    return pages


def chunk_page(page_dict: dict, chunk_size: int, chunk_overlap: int) -> list[dict]:
    text = page_dict["text"]
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "page": page_dict["page"],
                "filename": page_dict["filename"],
                "chunk_index": idx,
            })
            idx += 1
        start += chunk_size - chunk_overlap
    return chunks


def ingest_pdfs(pdf_paths: list[str], config: RAGConfig) -> int:
    config.persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(config.persist_dir))
    collection = client.get_or_create_collection(config.collection_name)
    embedder = SentenceTransformer(config.embed_model)

    all_chunks = []
    for path in pdf_paths:
        pages = load_pdf(path)
        for page_dict in pages:
            all_chunks.extend(chunk_page(page_dict, config.chunk_size, config.chunk_overlap))

    if not all_chunks:
        return 0

    ids = [f"{c['filename']}_p{c['page']}_c{c['chunk_index']}" for c in all_chunks]
    texts = [c["text"] for c in all_chunks]
    metadatas = [{"filename": c["filename"], "page": c["page"], "chunk_index": c["chunk_index"]} for c in all_chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True).tolist()

    collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    return len(all_chunks)


def get_indexed_files(config: RAGConfig) -> list[str]:
    if not config.persist_dir.exists():
        return []
    client = chromadb.PersistentClient(path=str(config.persist_dir))
    collection = client.get_or_create_collection(config.collection_name)
    results = collection.get(include=["metadatas"])
    filenames = sorted({m["filename"] for m in results["metadatas"]})
    return filenames
