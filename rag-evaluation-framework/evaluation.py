import os

from config import RAGConfig
from rag_chain import run_rag


def _token_f1(a: str, b: str) -> float:
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    common = ta & tb
    p = len(common) / len(ta)
    r = len(common) / len(tb)
    return 2 * p * r / (p + r) if (p + r) else 0.0


def compute_mrr(chunks: list[dict], expected_answer: str, threshold: float = 0.1) -> float:
    for rank, chunk in enumerate(chunks, 1):
        if _token_f1(chunk["text"], expected_answer) >= threshold:
            return 1.0 / rank
    return 0.0


# ── Fast local metrics (no LLM calls) ─────────────────────────────────────────
# Used when provider="ollama". Token-overlap approximations — complete in <1s.

def _local_faithfulness(answer: str, contexts: list[dict]) -> float:
    """Fraction of answer sentences supported by at least one context chunk."""
    sentences = [s.strip() for s in answer.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    if not sentences:
        return 0.0
    ctx_text = " ".join(c["text"] for c in contexts)
    supported = sum(1 for s in sentences if _token_f1(s, ctx_text) >= 0.1)
    return supported / len(sentences)


def _local_answer_relevancy(question: str, answer: str) -> float:
    """Token F1 overlap between question and answer."""
    return _token_f1(question, answer)


def _local_context_precision(question: str, contexts: list[dict]) -> float:
    """Fraction of retrieved chunks relevant to the question."""
    if not contexts:
        return 0.0
    relevant = sum(1 for c in contexts if _token_f1(question, c["text"]) >= 0.05)
    return relevant / len(contexts)


def _local_context_recall(contexts: list[dict], expected_answer: str) -> float:
    """Fraction of expected-answer tokens covered by retrieved chunks."""
    if not expected_answer.strip():
        return 0.0
    ctx_text = " ".join(c["text"] for c in contexts)
    return _token_f1(ctx_text, expected_answer)


def _run_local_evaluation(test_cases: list[dict], config: RAGConfig) -> list[dict]:
    results = []
    for i, case in enumerate(test_cases, 1):
        question = case["question"]
        expected = case.get("expected_answer", "")
        print(f"  [{i}/{len(test_cases)}] running RAG...", flush=True)
        rag_resp = run_rag(question, config)

        mrr = compute_mrr(rag_resp.contexts, expected)
        results.append({
            "question": question,
            "answer": rag_resp.answer,
            "retrieved_contexts": rag_resp.contexts,
            "faithfulness":       _local_faithfulness(rag_resp.answer, rag_resp.contexts),
            "answer_relevancy":   _local_answer_relevancy(question, rag_resp.answer),
            "context_precision":  _local_context_precision(question, rag_resp.contexts),
            "context_recall":     _local_context_recall(rag_resp.contexts, expected),
            "mrr": mrr,
        })
    return results


# ── Ragas evaluation (Anthropic / Groq providers) ──────────────────────────────

def _run_ragas_evaluation(
    test_cases: list[dict],
    config: RAGConfig,
    api_key: str | None = None,
) -> list[dict]:
    from langchain_community.embeddings import HuggingFaceEmbeddings as LCHuggingFaceEmbeddings
    from ragas import EvaluationDataset, SingleTurnSample, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness
    from ragas.run_config import RunConfig

    if config.provider == "groq":
        from langchain_groq import ChatGroq
        key = api_key or os.environ.get("GROQ_API_KEY", "")
        lc_llm = ChatGroq(model=config.groq_eval_model, api_key=key)
    else:
        from langchain_anthropic import ChatAnthropic
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        lc_llm = ChatAnthropic(model=config.haiku_model, api_key=key)

    llm = LangchainLLMWrapper(lc_llm)
    embeddings = LangchainEmbeddingsWrapper(LCHuggingFaceEmbeddings(model_name=config.embed_model))

    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=embeddings),
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
    ]

    per_question_results = []
    samples = []

    for case in test_cases:
        question = case["question"]
        expected = case.get("expected_answer", "")
        rag_resp = run_rag(question, config, api_key=api_key)
        mrr = compute_mrr(rag_resp.contexts, expected)
        samples.append(SingleTurnSample(
            user_input=question,
            retrieved_contexts=[c["text"] for c in rag_resp.contexts],
            response=rag_resp.answer,
            reference=expected,
        ))
        per_question_results.append({
            "question": question,
            "answer": rag_resp.answer,
            "retrieved_contexts": rag_resp.contexts,
            "mrr": mrr,
        })

    run_config = RunConfig(timeout=120, max_workers=2)
    dataset = EvaluationDataset(samples=samples)
    ragas_result = evaluate(dataset=dataset, metrics=metrics, llm=llm, embeddings=embeddings, run_config=run_config)
    ragas_df = ragas_result.to_pandas()

    for i, row in ragas_df.iterrows():
        per_question_results[i]["faithfulness"] = row.get("faithfulness")
        per_question_results[i]["answer_relevancy"] = row.get("answer_relevancy")
        per_question_results[i]["context_precision"] = row.get("context_precision")
        per_question_results[i]["context_recall"] = row.get("context_recall")

    return per_question_results


# ── Public API ──────────────────────────────────────────────────────────────────

def run_evaluation(
    test_cases: list[dict],
    config: RAGConfig,
    api_key: str | None = None,
) -> list[dict]:
    if config.provider == "ollama":
        return _run_local_evaluation(test_cases, config)
    return _run_ragas_evaluation(test_cases, config, api_key)  # anthropic or groq
