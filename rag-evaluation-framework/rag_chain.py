import os
import re
from dataclasses import dataclass, field

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
            citations.append({
                "ref": f"[{filename.strip()}, p.{page_str}]",
                "filename": filename.strip(),
                "page": int(page_str),
            })
    return citations


SYSTEM_PROMPT = (
    "You are a research assistant. Answer the user's question using ONLY the provided contexts below.\n"
    "IMPORTANT CITATION RULE: After every sentence that uses information from a context, you MUST add a citation "
    "in this exact format: [FILENAME, p.PAGE] — where FILENAME and PAGE come from the context header, "
    "for example: [attention_is_all_you_need.pdf, p.4]\n"
    "Do NOT use numeric citations like [1] or [2]. Only use the filename+page format above.\n"
    "If the contexts do not contain enough information, say so. Do not fabricate information."
)


def _call_anthropic(user_message: str, config: RAGConfig, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=config.generation_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def _call_ollama(user_message: str, config: RAGConfig) -> str:
    import ollama
    client = ollama.Client(host=config.ollama_base_url, timeout=config.ollama_timeout)
    response = client.chat(
        model=config.ollama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        options={"num_ctx": config.ollama_num_ctx},
    )
    return response.message.content


def _call_groq(user_message: str, config: RAGConfig, api_key: str) -> str:
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=config.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def run_rag(query: str, config: RAGConfig, api_key: str | None = None) -> RAGResponse:
    candidates = retrieve(query, config)
    contexts = rerank(query, candidates, config)
    user_message = build_prompt(query, contexts)

    if config.provider == "ollama":
        answer = _call_ollama(user_message, config)
    elif config.provider == "groq":
        key = api_key or os.environ.get("GROQ_API_KEY", "")
        answer = _call_groq(user_message, config, key)
    else:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        answer = _call_anthropic(user_message, config, key)

    citations = parse_citations(answer, contexts)
    return RAGResponse(answer=answer, citations=citations, contexts=contexts)
