import os

from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

from config import RAGConfig
from rag_chain import run_rag


def _token_f1(prediction: str, reference: str) -> float:
    pred_tokens = set(prediction.lower().split())
    ref_tokens = set(reference.lower().split())
    if not pred_tokens or not ref_tokens:
        return 0.0
    common = pred_tokens & ref_tokens
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_mrr(chunks: list[dict], expected_answer: str, threshold: float = 0.1) -> float:
    for rank, chunk in enumerate(chunks, 1):
        if _token_f1(chunk["text"], expected_answer) >= threshold:
            return 1.0 / rank
    return 0.0


def _get_ragas_llm(config: RAGConfig, api_key: str | None = None) -> LangchainLLMWrapper:
    if config.provider == "ollama":
        from langchain_ollama import ChatOllama
        lc_llm = ChatOllama(model=config.ollama_model, base_url=config.ollama_base_url)
    else:
        from langchain_anthropic import ChatAnthropic
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        lc_llm = ChatAnthropic(model=config.haiku_model, api_key=key)
    return LangchainLLMWrapper(lc_llm)


def run_evaluation(
    test_cases: list[dict],
    config: RAGConfig,
    api_key: str | None = None,
) -> list[dict]:
    llm = _get_ragas_llm(config, api_key)

    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm),
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
        context_texts = [c["text"] for c in rag_resp.contexts]

        samples.append(SingleTurnSample(
            user_input=question,
            retrieved_contexts=context_texts,
            response=rag_resp.answer,
            reference=expected,
        ))

        per_question_results.append({
            "question": question,
            "answer": rag_resp.answer,
            "retrieved_contexts": rag_resp.contexts,
            "mrr": mrr,
        })

    dataset = EvaluationDataset(samples=samples)
    ragas_result = evaluate(dataset=dataset, metrics=metrics, llm=llm)
    ragas_df = ragas_result.to_pandas()

    for i, row in ragas_df.iterrows():
        per_question_results[i]["faithfulness"] = row.get("faithfulness")
        per_question_results[i]["answer_relevancy"] = row.get("answer_relevancy")
        per_question_results[i]["context_precision"] = row.get("context_precision")
        per_question_results[i]["context_recall"] = row.get("context_recall")

    return per_question_results
