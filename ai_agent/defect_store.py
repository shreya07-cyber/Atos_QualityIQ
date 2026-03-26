"""
defect_store.py
---------------
SQLite-backed storage for defect metadata.

Regression logic:
  - Same-module regression: module tested twice, more failures in latest run
  - Cross-module regression: module A was passing, now module B test run
    causes module A scenarios to fail (detects side effects)
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "defects.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            module      TEXT    NOT NULL,
            scenario    TEXT    NOT NULL,
            result      TEXT    NOT NULL,
            reason      TEXT,
            matched     TEXT,
            timestamp   TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def store_result(module, scenario, result, reason="", matched=""):
    conn = _connect()
    conn.execute(
        "INSERT INTO defects (module,scenario,result,reason,matched,timestamp) VALUES (?,?,?,?,?,?)",
        (module, scenario, result, reason, matched,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()


def store_bulk(module, assertions):
    conn = _connect()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.executemany(
        "INSERT INTO defects (module,scenario,result,reason,matched,timestamp) VALUES (?,?,?,?,?,?)",
        [(module, a["scenario"], a["result"],
          a.get("reason",""), a.get("matched",""), ts) for a in assertions]
    )
    conn.commit()
    conn.close()


def get_all():
    conn = _connect()
    rows = conn.execute("SELECT * FROM defects ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_by_module(module):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM defects WHERE module=? ORDER BY id DESC", (module,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_run(module):
    conn = _connect()
    row = conn.execute(
        "SELECT MAX(timestamp) as ts FROM defects WHERE module=?", (module,)
    ).fetchone()
    if not row or not row["ts"]:
        conn.close()
        return []
    rows = conn.execute(
        "SELECT * FROM defects WHERE module=? AND timestamp=?",
        (module, row["ts"])
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_best_run(module):
    """
    Returns the run with the MOST passes for a module.
    Used as the baseline for cross-module regression.
    """
    conn = _connect()
    runs = conn.execute(
        "SELECT DISTINCT timestamp FROM defects WHERE module=? ORDER BY timestamp ASC",
        (module,)
    ).fetchall()
    conn.close()

    best_ts      = None
    best_passes  = -1

    for run in runs:
        ts = run["timestamp"]
        conn = _connect()
        passes = conn.execute(
            "SELECT COUNT(*) FROM defects WHERE module=? AND timestamp=? AND result='PASS'",
            (module, ts)
        ).fetchone()[0]
        conn.close()
        if passes > best_passes:
            best_passes = passes
            best_ts     = ts

    if not best_ts:
        return []
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM defects WHERE module=? AND timestamp=?",
        (module, best_ts)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_defect_density(module=None):
    conn = _connect()
    if module:
        total  = conn.execute("SELECT COUNT(*) FROM defects WHERE module=?", (module,)).fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM defects WHERE module=? AND result='FAIL'", (module,)).fetchone()[0]
    else:
        total  = conn.execute("SELECT COUNT(*) FROM defects").fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM defects WHERE result='FAIL'").fetchone()[0]
    conn.close()
    return round(failed / total, 4) if total > 0 else 0.0


def get_module_summary():
    conn = _connect()
    rows = conn.execute("""
        SELECT module,
               SUM(CASE WHEN result='PASS'  THEN 1 ELSE 0 END) as passed,
               SUM(CASE WHEN result='FAIL'  THEN 1 ELSE 0 END) as failed,
               SUM(CASE WHEN result='ERROR' THEN 1 ELSE 0 END) as errors,
               COUNT(*) as total
        FROM defects GROUP BY module
    """).fetchall()
    conn.close()
    return {r["module"]: dict(r) for r in rows}


def detect_regression(module):
    """
    Same-module regression:
    Compares last two runs of THIS module.
    Returns True if latest run has MORE failures than previous run.
    """
    conn = _connect()
    runs = conn.execute(
        "SELECT DISTINCT timestamp FROM defects WHERE module=? ORDER BY timestamp DESC LIMIT 2",
        (module,)
    ).fetchall()
    conn.close()

    if len(runs) < 2:
        return False

    latest_ts = runs[0]["timestamp"]
    prev_ts   = runs[1]["timestamp"]

    conn = _connect()
    latest_fails = conn.execute(
        "SELECT COUNT(*) FROM defects WHERE module=? AND timestamp=? AND result='FAIL'",
        (module, latest_ts)
    ).fetchone()[0]
    prev_fails = conn.execute(
        "SELECT COUNT(*) FROM defects WHERE module=? AND timestamp=? AND result='FAIL'",
        (module, prev_ts)
    ).fetchone()[0]
    conn.close()

    return latest_fails > prev_fails


def get_cross_module_regressions(current_module):
    """
    Cross-module regression check:
    After testing MODULE X, check if any OTHER modules that were
    previously all-passing now have failures in their latest run.

    Example:
      - LOGIN was tested and passed 100%
      - CART is now being tested
      - If LOGIN's latest results show new failures → regression!

    Returns list of dicts:
    [
      {
        "affected_module": "login",
        "scenario":        "Valid login with correct credentials",
        "was":             "PASS",
        "now":             "FAIL"
      },
      ...
    ]
    """
    conn = _connect()
    all_modules = [
        r[0] for r in
        conn.execute("SELECT DISTINCT module FROM defects").fetchall()
        if r[0] != current_module
    ]
    conn.close()

    regressions = []

    for module in all_modules:
        # Get the best historical run (most passes) as baseline
        best_run    = get_best_run(module)
        latest_run  = get_latest_run(module)

        if not best_run or not latest_run:
            continue

        # Build lookup: scenario → result for best run
        best_results = {r["scenario"]: r["result"] for r in best_run}

        # Check if any scenario that PASSED before now FAILS
        for record in latest_run:
            scenario      = record["scenario"]
            current_result = record["result"]
            previous_result = best_results.get(scenario)

            if previous_result == "PASS" and current_result == "FAIL":
                regressions.append({
                    "affected_module": module,
                    "scenario":        scenario,
                    "was":             "PASS",
                    "now":             "FAIL",
                })

    return regressions


def clear_all():
    conn = _connect()
    conn.execute("DELETE FROM defects")
    conn.commit()
    conn.close()


init_db()