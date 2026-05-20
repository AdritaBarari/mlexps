import os

from datasets import Dataset
from langchain_anthropic import ChatAnthropic
from ragas import evaluate
from ragas.metrics import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

from config import RAGConfig
from database import save_results
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


def run_evaluation(
    test_cases: list[dict],
    config: RAGConfig,
    api_key: str | None = None,
) -> list[dict]:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    llm = ChatAnthropic(model=config.haiku_model, api_key=key)

    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm),
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
    ]

    per_question_results = []
    ragas_rows = []

    for case in test_cases:
        question = case["question"]
        expected = case.get("expected_answer", "")
        rag_resp = run_rag(question, config, api_key=key)

        mrr = compute_mrr(rag_resp.contexts, expected)
        context_texts = [c["text"] for c in rag_resp.contexts]

        ragas_rows.append({
            "question": question,
            "answer": rag_resp.answer,
            "contexts": context_texts,
            "ground_truth": expected,
        })

        per_question_results.append({
            "question": question,
            "answer": rag_resp.answer,
            "retrieved_contexts": rag_resp.contexts,
            "mrr": mrr,
        })

    ragas_dataset = Dataset.from_list(ragas_rows)
    ragas_result = evaluate(ragas_dataset, metrics=metrics, llm=llm)
    ragas_df = ragas_result.to_pandas()

    for i, row in ragas_df.iterrows():
        per_question_results[i]["faithfulness"] = row.get("faithfulness")
        per_question_results[i]["answer_relevancy"] = row.get("answer_relevancy")
        per_question_results[i]["context_precision"] = row.get("context_precision")
        per_question_results[i]["context_recall"] = row.get("context_recall")

    return per_question_results
