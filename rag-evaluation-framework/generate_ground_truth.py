"""
Ground truth generator.
- Uses llama3.2 (3b) to generate Q&A pairs from ingested paper chunks.
- Runs each question through llama3.2:1b via the RAG pipeline.
- Saves all results to SQLite eval DB under a special "ground_truth" run.
- Also writes a JSON file for reuse in the Evaluate tab.

Usage:
    python generate_ground_truth.py --questions 50 --generator llama3.2 --rag-model llama3.2:1b
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import chromadb

sys.path.insert(0, str(Path(__file__).parent))

from config import RAGConfig
from database import init_db, save_results
from evaluation import run_evaluation

GT_PATH = Path(__file__).parent / "ground_truth.json"

GENERATE_PROMPT = """You are a research paper expert. Given the following excerpt from a research paper, generate {n} diverse, specific questions that can be answered directly from this excerpt.

For each question also provide the expected answer (1-3 sentences, factual, sourced from the excerpt).

Paper: {filename}, page {page}
Excerpt:
{text}

Respond in this exact JSON format (no other text):
[
  {{"question": "...", "expected_answer": "..."}},
  ...
]"""


def get_all_chunks(config: RAGConfig) -> list[dict]:
    client = chromadb.PersistentClient(path=str(config.persist_dir))
    collection = client.get_or_create_collection(config.collection_name)
    result = collection.get(include=["documents", "metadatas"])
    chunks = []
    for doc, meta in zip(result["documents"], result["metadatas"]):
        if len(doc.strip()) > 200:  # skip very short chunks
            chunks.append({"text": doc, "filename": meta["filename"], "page": meta["page"]})
    return chunks


def generate_qa_pairs(chunks: list[dict], total: int, generator_model: str, base_url: str) -> list[dict]:
    import ollama
    client = ollama.Client(host=base_url, timeout=180.0)

    pairs = []
    per_chunk = max(1, round(total / len(chunks)))
    sampled = random.sample(chunks, min(len(chunks), total))

    print(f"\nGenerating ~{total} Q&A pairs using {generator_model}...")
    for i, chunk in enumerate(sampled, 1):
        n = per_chunk if len(pairs) + per_chunk <= total else total - len(pairs)
        if n <= 0:
            break
        print(f"  [{i}/{len(sampled)}] {chunk['filename']} p.{chunk['page']} — asking for {n} Q&A(s)...", end=" ")
        try:
            resp = client.chat(
                model=generator_model,
                messages=[{"role": "user", "content": GENERATE_PROMPT.format(
                    n=n, filename=chunk["filename"], page=chunk["page"], text=chunk["text"][:1200]
                )}],
                options={"num_ctx": 3072},
            )
            raw = resp.message.content.strip()
            # extract JSON array even if surrounded by markdown fences
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start != -1 and end > start:
                items = json.loads(raw[start:end])
                valid = [x for x in items if x.get("question") and x.get("expected_answer")]
                pairs.extend(valid[:n])
                print(f"got {len(valid[:n])}")
            else:
                print("no JSON found, skipping")
        except Exception as e:
            print(f"error: {e}")

        if len(pairs) >= total:
            break

    return pairs[:total]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=int, default=50)
    parser.add_argument("--generator", default="llama3.2", help="Larger model for Q&A generation")
    parser.add_argument("--rag-model", default="llama3.2:1b", help="Smaller model for RAG execution")
    args = parser.parse_args()

    config = RAGConfig()
    chunks = get_all_chunks(config)
    print(f"Found {len(chunks)} usable chunks across {len(set(c['filename'] for c in chunks))} papers.")

    pairs = generate_qa_pairs(chunks, args.questions, args.generator, config.ollama_base_url)
    print(f"\nGenerated {len(pairs)} Q&A pairs. Saving to {GT_PATH}...")
    GT_PATH.write_text(json.dumps(pairs, indent=2))

    print(f"\nRunning RAG pipeline with {args.rag_model} on all {len(pairs)} questions...")
    rag_config = RAGConfig(ollama_model=args.rag_model)
    init_db(rag_config.db_path)

    t0 = time.time()
    results = run_evaluation(pairs, rag_config)
    elapsed = time.time() - t0

    run_id = save_results(results, rag_config.db_path)

    scores = {k: [r[k] for r in results if r.get(k) is not None]
              for k in ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "mrr"]}

    print(f"\n{'='*55}")
    print(f"Evaluation complete in {elapsed:.0f}s  |  run_id: {run_id[:8]}...")
    print(f"{'='*55}")
    for metric, vals in scores.items():
        avg = sum(vals) / len(vals) if vals else 0
        print(f"  {metric:<22} {avg:.3f}")
    print(f"\nResults saved to DB. Load in the Evaluate tab under History.")
    print(f"Ground truth JSON: {GT_PATH}")


if __name__ == "__main__":
    main()
