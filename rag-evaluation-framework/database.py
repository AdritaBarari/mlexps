import json
import sqlite3
import uuid
from datetime import datetime, timezone


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS evaluations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT NOT NULL,
    timestamp         TEXT NOT NULL,
    question          TEXT NOT NULL,
    answer            TEXT NOT NULL,
    retrieved_contexts TEXT NOT NULL,
    faithfulness      REAL,
    answer_relevancy  REAL,
    context_precision REAL,
    context_recall    REAL,
    mrr               REAL
);
"""


def init_db(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(CREATE_TABLE)
        conn.commit()


def save_results(results: list[dict], db_path: str) -> str:
    init_db(db_path)
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            run_id,
            timestamp,
            r["question"],
            r["answer"],
            json.dumps(r["retrieved_contexts"]),
            r.get("faithfulness"),
            r.get("answer_relevancy"),
            r.get("context_precision"),
            r.get("context_recall"),
            r.get("mrr"),
        )
        for r in results
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO evaluations "
            "(run_id, timestamp, question, answer, retrieved_contexts, "
            "faithfulness, answer_relevancy, context_precision, context_recall, mrr) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    return run_id


def load_results(db_path: str, run_id: str | None = None) -> list[dict]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if run_id:
            rows = conn.execute(
                "SELECT * FROM evaluations WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM evaluations ORDER BY id").fetchall()
    results = []
    for row in rows:
        r = dict(row)
        r["retrieved_contexts"] = json.loads(r["retrieved_contexts"])
        results.append(r)
    return results


def list_run_ids(db_path: str) -> list[dict]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT run_id, timestamp, COUNT(*) as num_questions "
            "FROM evaluations GROUP BY run_id ORDER BY timestamp DESC"
        ).fetchall()
    return [{"run_id": r[0], "timestamp": r[1], "num_questions": r[2]} for r in rows]
