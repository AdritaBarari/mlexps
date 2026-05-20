"""Full end-to-end test: ingest → retrieve → rerank → llama3.2:1b generation."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import RAGConfig
from rag_chain import run_rag

config = RAGConfig()
print(f"Provider : {config.provider}")
print(f"Model    : {config.ollama_model}")
print(f"Timeout  : {config.ollama_timeout}s\n")

queries = [
    "What is the attention mechanism and why is it useful?",
    "What BLEU score did the Transformer achieve on WMT 2014 English-to-German?",
]

for query in queries:
    print("=" * 60)
    print(f"Q: {query}\n")
    t0 = time.time()
    resp = run_rag(query, config)
    elapsed = time.time() - t0
    print(f"A: {resp.answer}\n")
    print(f"Citations : {[c['ref'] for c in resp.citations]}")
    print(f"Top chunk : {resp.contexts[0]['filename']}, p.{resp.contexts[0]['page']} "
          f"(rerank: {resp.contexts[0].get('rerank_score', 0):.2f})")
    print(f"Time      : {elapsed:.1f}s\n")
