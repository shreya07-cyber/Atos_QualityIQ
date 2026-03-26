"""
history_store.py
----------------
Stores test run history per story/feature.
Tracks failure counts, reasons, timestamps.
Used for prioritization and adaptive depth.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "history.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id     TEXT    NOT NULL,
            feature      TEXT    NOT NULL,
            scenario     TEXT    NOT NULL,
            status       TEXT    NOT NULL,
            reason       TEXT,
            timestamp    TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def store_run(story_id: str, feature: str, results: list):
    """
    Store all results from a test run.
    results = [{"scenario": ..., "result": ..., "reason": ...}, ...]
    """
    conn  = _connect()
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows  = [
        (story_id, feature, r["scenario"],
         r["result"], r.get("reason",""), ts)
        for r in results
    ]
    conn.executemany(
        "INSERT INTO history (story_id,feature,scenario,status,reason,timestamp) VALUES (?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    conn.close()


def get_failure_count(feature: str, scenario: str = None) -> int:
    """
    Returns how many times a feature (or specific scenario) has failed historically.
    """
    conn = _connect()
    if scenario:
        count = conn.execute(
            "SELECT COUNT(*) FROM history WHERE feature=? AND scenario=? AND status='FAIL'",
            (feature, scenario)
        ).fetchone()[0]
    else:
        count = conn.execute(
            "SELECT COUNT(*) FROM history WHERE feature=? AND status='FAIL'",
            (feature,)
        ).fetchone()[0]
    conn.close()
    return count


def get_feature_summary(feature: str) -> dict:
    """Returns total/pass/fail counts for a feature across all history."""
    conn  = _connect()
    total = conn.execute("SELECT COUNT(*) FROM history WHERE feature=?", (feature,)).fetchone()[0]
    fails = conn.execute("SELECT COUNT(*) FROM history WHERE feature=? AND status='FAIL'", (feature,)).fetchone()[0]
    conn.close()
    return {
        "feature":       feature,
        "total_runs":    total,
        "total_failures": fails,
        "failure_rate":  round(fails / total, 3) if total else 0.0,
        "frequent":      fails >= 3,   # flag: this feature fails a lot
    }


def get_all_feature_summaries() -> dict:
    conn  = _connect()
    feats = [r[0] for r in conn.execute("SELECT DISTINCT feature FROM history").fetchall()]
    conn.close()
    return {f: get_feature_summary(f) for f in feats}


def get_failing_scenarios(feature: str) -> list:
    """Returns scenarios that have failed at least once, sorted by failure count."""
    conn  = _connect()
    rows  = conn.execute("""
        SELECT scenario, COUNT(*) as fail_count
        FROM history
        WHERE feature=? AND status='FAIL'
        GROUP BY scenario
        ORDER BY fail_count DESC
    """, (feature,)).fetchall()
    conn.close()
    return [{"scenario": r["scenario"], "fail_count": r["fail_count"]} for r in rows]


def clear_all():
    conn = _connect()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()


init_db()