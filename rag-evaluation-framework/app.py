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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global fonts ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.01em;
}

/* ── Headings ── */
h1, h2, h3, h4 {
    font-family: 'Sora', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* ── App title ── */
.stApp h1 {
    font-size: 1.8rem !important;
    background: linear-gradient(90deg, #4F8EF7, #A78BFA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    padding-bottom: 0.2rem;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0D1117 !important;
    border-right: 1px solid #21262D !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em !important;
    color: #8B949E !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em !important;
    color: #8B949E !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #4F8EF7 !important;
    border-bottom-color: #4F8EF7 !important;
}

/* ── Cards / containers ── */
[data-testid="stExpander"] {
    background-color: #161B22 !important;
    border: 1px solid #21262D !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: #8B949E !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background-color: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em !important;
    color: #8B949E !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Sora', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #4F8EF7 !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.07em !important;
    background-color: #4F8EF7 !important;
    color: #0D1117 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.45rem 1.2rem !important;
    transition: opacity 0.15s ease !important;
}
.stButton > button:hover {
    opacity: 0.85 !important;
}

/* ── Text input ── */
.stTextInput > div > div > input {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 6px !important;
    color: #E6EDF3 !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4F8EF7 !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.15) !important;
}

/* ── Code / pre blocks (citations, context) ── */
pre, code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    background-color: #161B22 !important;
    border: 1px solid #21262D !important;
    border-radius: 6px !important;
}

/* ── Captions ── */
.stCaption, [data-testid="stCaptionContainer"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em !important;
    color: #8B949E !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #21262D !important;
    border-radius: 8px !important;
    overflow: hidden;
}

/* ── Divider ── */
hr {
    border-color: #21262D !important;
    margin: 1.2rem 0 !important;
}

/* ── Success / warning / error banners ── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)


def get_api_key() -> str:
    return st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))


@st.cache_data(ttl=60)
def _ollama_available() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


def get_config() -> RAGConfig:
    default_provider = "ollama" if _ollama_available() else "anthropic"
    provider = st.session_state.get("provider", default_provider)
    ollama_model = st.session_state.get("ollama_model", "llama3.2:1b")
    return RAGConfig(provider=provider, ollama_model=ollama_model)


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

# ── Sidebar: provider settings ────────────────────────────────────────────────
with st.sidebar:
    st.header("LLM Provider")
    provider = st.radio("Provider", ["ollama", "anthropic"],
                        index=0, key="provider")

    if provider == "ollama":
        st.text_input("Ollama model", value="llama3.2:1b", key="ollama_model",
                      help="Run `ollama pull <model>` first. E.g. llama3.2, mistral, qwen2.5")
        st.caption("Make sure Ollama is running: `ollama serve`")
    else:
        api_key_input = st.text_input("Anthropic API key", type="password",
                                      value=get_api_key(),
                                      help="Or set ANTHROPIC_API_KEY in .streamlit/secrets.toml")
        if api_key_input:
            os.environ["ANTHROPIC_API_KEY"] = api_key_input

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
        if config.provider == "anthropic" and not api_key:
            st.error("ANTHROPIC_API_KEY not set. Add it to .streamlit/secrets.toml or the Streamlit Cloud dashboard.")
        else:
            spinner_msg = "Retrieving and generating answer… (Ollama on CPU: ~20–60s)" if config.provider == "ollama" else "Retrieving and generating answer…"
            with st.spinner(spinner_msg):
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
            if config.provider == "anthropic" and not api_key:
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
