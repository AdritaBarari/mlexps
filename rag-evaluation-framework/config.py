from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RAGConfig:
    generation_model: str = "claude-sonnet-4-6"
    haiku_model: str = "claude-haiku-4-5-20251001"
    embed_model: str = "all-MiniLM-L6-v2"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_k: int = 15
    rerank_top_n: int = 5
    persist_dir: Path = field(default_factory=lambda: Path(__file__).parent / "chroma_store")
    collection_name: str = "research_papers"
    db_path: str = field(default_factory=lambda: str(Path(__file__).parent / "eval_results.db"))
