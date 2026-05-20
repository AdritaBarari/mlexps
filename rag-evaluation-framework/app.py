import os
import re
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from config import RAGConfig
from database import init_db, list_run_ids, load_results, save_results
from evaluation import run_evaluation
from ingestion import get_indexed_files, ingest_pdfs
from rag_chain import run_rag

st.set_page_config(page_title="Research RAG", page_icon="📚", layout="wide")


def get_api_key() -> str:
    return st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))


@st.cache_resource
def get_config() -> RAGConfig:
    return RAGConfig()


def bold_citations(text: str) -> str:
    return re.sub(r"(\[[^\]]+,\s*p\.\d+\])", r"**\1**", text)


def display_results(results: list[dict]) -> None:
    metric_keys = ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "mrr"]
    labels = ["Faithfulness", "Ans. Relevancy", "Ctx. Precision", "Ctx. Recall", "MRR"]

    def _mean(key: str) -> float:
        vals = [r[key] for r in results if r.get(key) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    cols = st.columns(len(metric_keys))
    for col, key, label in zip(cols, metric_keys, labels):
        col.metric(label, f"{_mean(key):.3f}")

    chart_data = pd.DataFrame({"Score": [_mean(k) for k in metric_keys]}, index=labels)
    st.bar_chart(chart_data)

    display_df = pd.DataFrame([
        {
            "Question": r["question"],
            "Faithfulness": r.get("faithfulness"),
            "Ans. Relevancy": r.get("answer_relevancy"),
            "Ctx. Precision": r.get("context_precision"),
            "Ctx. Recall": r.get("context_recall"),
            "MRR": r.get("mrr"),
        }
        for r in results
    ])
    st.dataframe(display_df, use_container_width=True)


# ── App bootstrap ─────────────────────────────────────────────────────────────
config = get_config()
db_path = config.db_path
init_db(db_path)

st.title("📚 Research Paper RAG")

tab_upload, tab_ask, tab_eval = st.tabs(["Upload Papers", "Ask Questions", "Evaluate"])

# ── Upload tab ────────────────────────────────────────────────────────────────
with tab_upload:
    st.subheader("Index Research Papers")

    indexed = get_indexed_files(config)
    if indexed:
        st.success(f"{len(indexed)} paper(s) currently indexed: {', '.join(indexed)}")
    else:
        st.warning("No papers indexed yet. Upload PDFs to get started.")

    uploaded_files = st.file_uploader(
        "Upload PDF papers", type=["pdf"], accept_multiple_files=True
    )

    if uploaded_files and st.button("Ingest Papers"):
        tmp_paths = []
        for uf in uploaded_files:
            dest = Path(tempfile.gettempdir()) / uf.name
            dest.write_bytes(uf.read())
            tmp_paths.append(str(dest))

        with st.spinner(f"Ingesting {len(tmp_paths)} file(s)…"):
            n_chunks = ingest_pdfs(tmp_paths, config)

        for p in tmp_paths:
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass

        st.success(f"Done — {n_chunks} chunks indexed.")
        st.cache_resource.clear()
        st.rerun()

# ── Ask tab ───────────────────────────────────────────────────────────────────
with tab_ask:
    st.subheader("Ask a Question")

    if "history" not in st.session_state:
        st.session_state.history = []

    query = st.text_input("Your question", placeholder="e.g. What is the attention mechanism?")

    if st.button("Ask") and query.strip():
        api_key = get_api_key()
        if not api_key:
            st.error("ANTHROPIC_API_KEY not set. Add it to .streamlit/secrets.toml or the Streamlit Cloud dashboard.")
        else:
            with st.spinner("Retrieving and generating answer…"):
                response = run_rag(query, config, api_key=api_key)
            st.session_state.history.append({"query": query, "response": response})

    for turn in reversed(st.session_state.history):
        st.divider()
        st.markdown(f"**Q:** {turn['query']}")
        resp = turn["response"]

        col_answer, col_context = st.columns([0.65, 0.35])

        with col_answer:
            st.markdown("**Answer:**")
            st.markdown(bold_citations(resp.answer))
            if resp.citations:
                st.markdown("**Sources:**")
                for c in resp.citations:
                    st.markdown(f"- {c['ref']}")

        with col_context:
            with st.expander("Retrieved Contexts", expanded=False):
                for chunk in resp.contexts:
                    st.caption(
                        f"{chunk['filename']} — p.{chunk['page']}  |  "
                        f"rerank score: {chunk.get('rerank_score', 0):.3f}"
                    )
                    st.text(chunk["text"][:600] + ("…" if len(chunk["text"]) > 600 else ""))
                    st.divider()

# ── Evaluate tab ──────────────────────────────────────────────────────────────
with tab_eval:
    st.subheader("RAG Evaluation")

    default_cases = pd.DataFrame([{"question": "", "expected_answer": ""}])
    test_df = st.data_editor(
        default_cases,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "question": st.column_config.TextColumn("Question", width="large"),
            "expected_answer": st.column_config.TextColumn("Expected Answer", width="large"),
        },
    )

    if st.button("Run Evaluation"):
        test_cases = [
            {"question": row["question"], "expected_answer": row["expected_answer"]}
            for _, row in test_df.iterrows()
            if str(row["question"]).strip()
        ]
        if not test_cases:
            st.warning("Add at least one question before running evaluation.")
        else:
            api_key = get_api_key()
            if not api_key:
                st.error("ANTHROPIC_API_KEY not set.")
            else:
                with st.spinner(f"Evaluating {len(test_cases)} question(s)…"):
                    results = run_evaluation(test_cases, config, api_key=api_key)
                run_id = save_results(results, db_path)
                st.session_state["last_eval_results"] = results
                st.session_state["last_eval_run_id"] = run_id
                st.success(f"Evaluation complete. Run ID: `{run_id}`")

    if "last_eval_results" in st.session_state:
        display_results(st.session_state["last_eval_results"])

    st.divider()
    st.subheader("Evaluation History")
    run_list = list_run_ids(db_path)
    if run_list:
        options = {
            f"{r['timestamp'][:19]}  ({r['num_questions']} Q)  —  {r['run_id'][:8]}…": r["run_id"]
            for r in run_list
        }
        selected_label = st.selectbox("Load a past run", list(options.keys()))
        if st.button("Load"):
            past_results = load_results(db_path, run_id=options[selected_label])
            display_results(past_results)
    else:
        st.info("No evaluation runs recorded yet.")
