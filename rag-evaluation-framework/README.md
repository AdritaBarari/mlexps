# RAG Evaluation Framework

A local, fully offline RAG (Retrieval-Augmented Generation) system for querying research papers with inline citations. Includes a two-stage retrieval pipeline, Ragas-based evaluation, and a Streamlit UI.

Supports two LLM backends: **Ollama** (local, no API key needed) and **Anthropic Claude** (cloud).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI  (app.py)                   │
│          Upload Papers │ Ask Questions │ Evaluate               │
└──────────┬─────────────────────────┬───────────────────────────-┘
           │                         │
           ▼                         ▼
  ┌─────────────────┐      ┌─────────────────────────────────────┐
  │  ingestion.py   │      │           rag_chain.py              │
  │  ─────────────  │      │  ─────────────────────────────────  │
  │  PyMuPDF →      │      │  build_prompt()                     │
  │  chunk_page() → │      │  run_rag() ──► retriever.py         │
  │  SentenceXform  │      │           └──► reranker.py          │
  │  embeddings  →  │      │           └──► Ollama / Claude      │
  │  ChromaDB upsert│      │           └──► parse_citations()    │
  └────────┬────────┘      └──────────────────┬──────────────────┘
           │                                  │
           ▼                                  ▼
  ┌─────────────────┐              ┌──────────────────┐
  │  ChromaDB       │◄─────────────│  retriever.py    │
  │  (chroma_store/)│  bi-encoder  │  15 candidates   │
  └─────────────────┘  vector query└────────┬─────────┘
                                            │
                                            ▼
                                   ┌──────────────────┐
                                   │  reranker.py     │
                                   │  cross-encoder   │
                                   │  → top 5 chunks  │
                                   └──────────────────┘

  Evaluation path:
  ┌────────────────────────────────────────────────────┐
  │  evaluation.py                                     │
  │  ─────────────────────────────────────────────     │
  │  run_evaluation(test_cases)                        │
  │    └── run_rag() per question                      │
  │    └── compute_mrr()  (token F1 overlap)           │
  │    └── Ragas evaluate()                            │
  │         ├── Faithfulness                           │
  │         ├── AnswerRelevancy                        │
  │         ├── ContextPrecision                       │
  │         └── ContextRecall                          │
  │    └── save_results() → SQLite                     │
  └────────────────────────────────────────────────────┘
```

### Query Sequence

```
User query
    │
    ▼
retriever.py  ──  bi-encoder (all-MiniLM-L6-v2)
                  ChromaDB.query(n=15)             ← wide recall set
    │
    ▼
reranker.py   ──  cross-encoder (ms-marco-MiniLM-L-6-v2)
                  score each [query, chunk] pair
                  return top 5                     ← precision filter
    │
    ▼
rag_chain.py  ──  numbered context prompt
                  Ollama (llama3.2:1b) or Claude
                  parse [Filename, p.N] citations
    │
    ▼
RAGResponse   ──  answer + citations + raw contexts
```

---

## Modules

### `config.py`
Central configuration dataclass. All tunable parameters live here — no magic strings scattered across the codebase.

| Field | Default | Description |
|---|---|---|
| `provider` | `"ollama"` | `"ollama"` or `"anthropic"` |
| `generation_model` | `"claude-sonnet-4-6"` | Anthropic model for generation |
| `haiku_model` | `"claude-haiku-4-5-20251001"` | Anthropic model for Ragas evaluation |
| `ollama_model` | `"llama3.2:1b"` | Local Ollama model |
| `ollama_base_url` | `"http://localhost:11434"` | Ollama server URL |
| `ollama_timeout` | `120.0` | Generation timeout (seconds) |
| `ollama_num_ctx` | `2048` | Context window tokens |
| `embed_model` | `"all-MiniLM-L6-v2"` | Bi-encoder for retrieval |
| `rerank_model` | `"cross-encoder/ms-marco-MiniLM-L-6-v2"` | Cross-encoder for reranking |
| `chunk_size` | `512` | Characters per chunk |
| `chunk_overlap` | `64` | Overlap between consecutive chunks |
| `retrieval_k` | `15` | Candidates fetched from ChromaDB |
| `rerank_top_n` | `5` | Final chunks passed to the LLM |
| `persist_dir` | `./chroma_store` | ChromaDB storage path |
| `db_path` | `./eval_results.db` | SQLite evaluation results |

---

### `ingestion.py`
Handles PDF loading, chunking, embedding, and ChromaDB storage.

**Functions:**

- **`load_pdf(path) → list[dict]`**  
  Opens a PDF with PyMuPDF (`fitz`), extracts text page by page. Returns `[{text, page, filename}]`.

- **`chunk_page(page_dict, chunk_size, overlap) → list[dict]`**  
  Sliding-window chunking over a single page's text. Returns `[{text, page, filename, chunk_index}]`.

- **`ingest_pdfs(pdf_paths, config) → int`**  
  Full ingestion pipeline: load → chunk all pages → embed with SentenceTransformer → upsert to ChromaDB. Returns the total number of chunks stored.  
  IDs are deterministic (`{filename}_p{page}_c{chunk_index}`) so re-ingesting the same PDF is idempotent.

- **`get_indexed_files(config) → list[str]`**  
  Returns sorted list of unique filenames already stored in ChromaDB.

---

### `retriever.py`
First-stage retrieval using bi-encoder vector search.

**Why bi-encoder here:** SentenceTransformer encodes the query and all document chunks independently into a shared embedding space. Fast enough for large-scale first-pass retrieval (milliseconds). Returns a wide candidate set (`retrieval_k=15`) optimised for recall.

- **`retrieve(query, config) → list[dict]`**  
  Embeds the query, calls `ChromaDB.query(n_results=retrieval_k)`, returns `[{text, filename, page, score}]` where `score = 1 - cosine_distance`.

`_get_embedder()` is `@lru_cache`-wrapped so the 80 MB SentenceTransformer model loads once per process.

---

### `reranker.py`
Second-stage precision filter using a cross-encoder.

**Why cross-encoder here:** Unlike bi-encoders, a cross-encoder sees the query and passage *together*, enabling token-level attention between them. This produces significantly more accurate relevance scores but is too slow for first-pass retrieval over thousands of chunks. The two-stage pattern (fast bi-encoder → accurate cross-encoder) is the industry standard.

- **`rerank(query, chunks, config) → list[dict]`**  
  Scores every `[query, chunk]` pair with the cross-encoder. Sorts descending, returns top `rerank_top_n=5`. Adds `rerank_score` to each returned chunk.

`_get_cross_encoder()` is `@lru_cache`-wrapped to avoid reloading 100+ weight files on every query.

---

### `rag_chain.py`
Orchestrates retrieval → reranking → generation → citation parsing.

**Key functions:**

- **`build_prompt(query, contexts) → str`**  
  Formats numbered context blocks as `Context [N] — filename, p.page:\n{text}` followed by the question.

- **`parse_citations(answer, contexts) → list[dict]`**  
  Regex `r"\[([^,\]]+),\s*p\.(\d+)\]"` extracts `[Filename, p.N]` references from the generated answer. Deduplicates by `(filename, page)`.

- **`run_rag(query, config, api_key) → RAGResponse`**  
  Full pipeline: `retrieve → rerank → build_prompt → LLM → parse_citations`.

- **`_call_ollama(message, config)`** / **`_call_anthropic(message, config, api_key)`**  
  Provider-specific generation calls. Ollama uses `ollama.Client` with `num_ctx` and `timeout` options.

**`RAGResponse`** dataclass:
```python
answer:    str          # generated text with [File, p.N] citations inline
citations: list[dict]   # [{"ref": "[Paper, p.4]", "filename": str, "page": int}]
contexts:  list[dict]   # raw reranked chunks with rerank_score
```

**System prompt strategy:** The LLM is instructed to cite every factual sentence using `[FILENAME, p.PAGE]` format (not numeric `[1]`) and to say "I don't know" when context is insufficient. This is especially important for small models like `llama3.2:1b`.

---

### `evaluation.py`
Computes Ragas metrics and MRR over a set of test Q&A pairs.

**Metrics computed:**

| Metric | What it measures |
|---|---|
| **Faithfulness** | Does the answer contain only claims supported by the retrieved contexts? |
| **Answer Relevancy** | Is the answer relevant to the question? (uses embeddings) |
| **Context Precision** | Are the retrieved chunks relevant to the question? |
| **Context Recall** | Do the retrieved chunks cover the ground-truth answer? |
| **MRR** (Mean Reciprocal Rank) | Is the most relevant chunk ranked near the top? |

**Key functions:**

- **`compute_mrr(chunks, expected_answer, threshold=0.1) → float`**  
  For each chunk in rank order, computes token-overlap F1 between chunk text and the expected answer. Returns `1/rank` of the first chunk exceeding the threshold, or `0.0` if none qualify.

- **`run_evaluation(test_cases, config, api_key) → list[dict]`**  
  Runs `run_rag()` for each test case, collects Ragas `SingleTurnSample` objects, calls `ragas.evaluate()` with `RunConfig(timeout=300, max_workers=1)` (serial execution required for Ollama on CPU), and merges per-row metric values back into the results.

Uses **Ragas 0.4.x API**: `EvaluationDataset`, `SingleTurnSample`, `LangchainLLMWrapper`, and `ragas.embeddings.HuggingFaceEmbeddings`. The embeddings wrapper uses the same `all-MiniLM-L6-v2` model as retrieval to avoid downloading a second model.

---

### `database.py`
SQLite persistence for evaluation runs. Uses Python's built-in `sqlite3` — no ORM.

**Schema:**
```sql
CREATE TABLE evaluations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT NOT NULL,      -- uuid4, groups all rows from one eval run
    timestamp         TEXT NOT NULL,      -- ISO-8601 UTC
    question          TEXT NOT NULL,
    answer            TEXT NOT NULL,
    retrieved_contexts TEXT NOT NULL,     -- JSON: [{text, filename, page, rerank_score}]
    faithfulness      REAL,
    answer_relevancy  REAL,
    context_precision REAL,
    context_recall    REAL,
    mrr               REAL
);
```

**Functions:**
- `init_db(db_path)` — creates table if not exists
- `save_results(results, db_path) → str` — inserts all rows under a new `run_id`, returns the `run_id`
- `load_results(db_path, run_id=None) → list[dict]` — returns all rows or filtered by `run_id`; deserialises `retrieved_contexts` JSON
- `list_run_ids(db_path) → list[dict]` — returns `[{run_id, timestamp, num_questions}]` sorted newest-first, used to populate the History dropdown

---

### `app.py`
Streamlit UI with three tabs. Dark corporate theme with Google Fonts (Sora / Inter / JetBrains Mono) injected via `st.markdown(..., unsafe_allow_html=True)`.

**Sidebar:** Provider radio (`ollama` / `anthropic`) + model name input. Config is read on every rerender via `get_config()` from `st.session_state`.

**Upload Papers tab:**
- Shows currently indexed files from ChromaDB
- `st.file_uploader` (multi-file, PDF only) → writes to `tempfile` (Windows-safe) → `ingest_pdfs()` → clears Streamlit resource cache → reruns

**Ask Questions tab:**
- Text input + Ask button → `run_rag()` with spinner
- Two-column layout: answer + bolded citations (left 65%) | expandable retrieved chunks with rerank scores (right 35%)
- `st.session_state.history` preserves all Q&A turns for the session

**Evaluate tab:**
- `st.data_editor` for entering Q&A test pairs (dynamic rows)
- Run Evaluation → `run_evaluation()` → `save_results()` → `display_results()`
- `display_results()` renders: 5 metric cards, bar chart, per-question dataframe
- History section: `st.selectbox` over past `run_id`s → Load button → re-renders the same metric view

---

### `generate_ground_truth.py`
CLI script for automated ground truth generation. Uses a larger model to generate Q&A pairs from the indexed paper chunks, then benchmarks the full RAG pipeline against them.

**Usage:**
```
python generate_ground_truth.py --questions 50 --generator llama3.2 --rag-model llama3.2:1b
```

**Flow:**
1. Fetches all chunks from ChromaDB (filters out chunks < 200 chars)
2. Samples chunks uniformly, prompts `--generator` model to produce `[{question, expected_answer}]` JSON for each
3. Saves Q&A pairs to `ground_truth.json`
4. Runs `run_evaluation()` on all pairs using `--rag-model`
5. Saves results to SQLite and prints a metric summary

Expected runtime: ~30–60 min for 50 questions on CPU (`llama3.2:3b` generator + `llama3.2:1b` RAG executor).

---

## Setup

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- Models pulled: `ollama pull llama3.2:1b` (RAG) and `ollama pull llama3.2` (ground truth generation)

### Install
```bash
python -m venv rag-env
# Windows:
rag-env\Scripts\activate
# macOS/Linux:
source rag-env/bin/activate

pip install -r rag-evaluation-framework/requirements.txt
```

### Run locally
```bash
streamlit run rag-evaluation-framework/app.py
```

### API key (Anthropic provider only)
Create `.streamlit/secrets.toml` (git-ignored):
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## Deployment (Streamlit Community Cloud)

1. Push repo to GitHub (`.streamlit/secrets.toml` and `chroma_store/` are git-ignored)
2. Connect repo in Streamlit Cloud, set main file to `rag-evaluation-framework/app.py`
3. Add `ANTHROPIC_API_KEY` under Settings → Secrets
4. Upload papers via the Upload tab after each deploy

**Note:** Streamlit Cloud's filesystem is ephemeral — ChromaDB and SQLite are wiped on redeploy/restart. Re-upload papers each session.

---

## File Structure

```
rag-evaluation-framework/
├── config.py                  # RAGConfig dataclass
├── ingestion.py               # PDF load, chunk, embed, ChromaDB upsert
├── retriever.py               # Bi-encoder vector search (top-15 recall)
├── reranker.py                # Cross-encoder reranker (top-5 precision)
├── rag_chain.py               # Prompt builder, LLM caller, citation parser
├── evaluation.py              # Ragas 0.4.x + MRR evaluation runner
├── database.py                # SQLite init / save / load
├── app.py                     # Streamlit UI
├── generate_ground_truth.py   # CLI: auto-generate Q&A benchmark + run eval
├── requirements.txt           # Python dependencies
└── README.md                  # This file

.streamlit/
├── config.toml                # Dark theme settings
└── secrets.toml               # API key (git-ignored)
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `anthropic` | Claude API client |
| `ollama` | Ollama Python client |
| `pymupdf` | PDF text extraction |
| `sentence-transformers` | Bi-encoder embeddings + cross-encoder reranking |
| `chromadb` | Vector store |
| `ragas` | RAG evaluation metrics (0.4.x API) |
| `langchain-ollama` | LangChain wrapper for Ollama (Ragas LLM bridge) |
| `langchain-anthropic` | LangChain wrapper for Claude (Ragas LLM bridge) |
| `langchain-community` | HuggingFace embeddings wrapper |
| `datasets` | Required by Ragas internally |
| `pandas` | Dataframe display in Streamlit |
