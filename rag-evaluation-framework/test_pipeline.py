"""
Quick end-to-end test: ingest a PDF, retrieve + rerank for a query.
Run from the rag-evaluation-framework directory.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import RAGConfig
from ingestion import ingest_pdfs, get_indexed_files
from retriever import retrieve
from reranker import rerank

PDF = str(Path(__file__).parent / "attention_is_all_you_need.pdf")
config = RAGConfig()

print("=" * 60)
print("STEP 1: Ingesting paper...")
n = ingest_pdfs([PDF], config)
print(f"  Indexed {n} chunks from {Path(PDF).name}")

print("\nSTEP 2: Indexed files in ChromaDB:")
for f in get_indexed_files(config):
    print(f"  - {f}")

queries = [
    "What is the attention mechanism?",
    "How does multi-head attention work?",
    "What are the results on WMT translation tasks?",
]

for query in queries:
    print(f"\n{'=' * 60}")
    print(f"QUERY: {query}")

    candidates = retrieve(query, config)
    print(f"  Retrieved {len(candidates)} candidates")

    reranked = rerank(query, candidates, config)
    print(f"  Top {len(reranked)} after reranking:\n")

    for i, chunk in enumerate(reranked, 1):
        score = chunk.get("rerank_score", 0)
        print(f"  [{i}] {chunk['filename']}, p.{chunk['page']}  (rerank score: {score:.3f})")
        preview = chunk['text'][:200].strip().encode('ascii', errors='replace').decode()
        print(f"      {preview}...")
        print()

print("=" * 60)
print("Pipeline test complete. LLM generation skipped (install Ollama to test full RAG).")
