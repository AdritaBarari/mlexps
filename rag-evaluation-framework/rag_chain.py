import os
import re
from dataclasses import dataclass, field

import anthropic

from config import RAGConfig
from retriever import retrieve
from reranker import rerank


@dataclass
class RAGResponse:
    answer: str
    citations: list[dict]
    contexts: list[dict]


def build_prompt(query: str, contexts: list[dict]) -> str:
    context_blocks = []
    for i, ctx in enumerate(contexts, 1):
        context_blocks.append(
            f"Context [{i}] — {ctx['filename']}, p.{ctx['page']}:\n{ctx['text']}"
        )
    joined = "\n\n".join(context_blocks)
    return f"{joined}\n\nQuestion: {query}"


def parse_citations(answer: str, contexts: list[dict]) -> list[dict]:
    pattern = r"\[([^,\]]+),\s*p\.(\d+)\]"
    matches = re.findall(pattern, answer)
    seen = set()
    citations = []
    for filename, page_str in matches:
        key = (filename.strip(), int(page_str))
        if key not in seen:
            seen.add(key)
            citations.append({"ref": f"[{filename.strip()}, p.{page_str}]", "filename": filename.strip(), "page": int(page_str)})
    return citations


def run_rag(query: str, config: RAGConfig, api_key: str | None = None) -> RAGResponse:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=key)

    candidates = retrieve(query, config)
    contexts = rerank(query, candidates, config)

    system_prompt = (
        "You are a research assistant. Answer the user's question using ONLY the provided contexts. "
        "Cite every factual claim using the format [Filename, p.N] referencing the context number above. "
        "If the contexts do not contain enough information to answer, say so — do not fabricate information."
    )

    user_message = build_prompt(query, contexts)

    response = client.messages.create(
        model=config.generation_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    answer = response.content[0].text
    citations = parse_citations(answer, contexts)
    return RAGResponse(answer=answer, citations=citations, contexts=contexts)
