# Person 3 — Automation + Risk Engine + Dashboard

## 🚀 Setup

```bash
cd ai_agent
pip install playwright streamlit pandas
playwright install chromium
```

---

## ▶️ Run the Dashboard

```bash
# Make sure Person 1's demo site is already running on localhost:5000
streamlit run dashboard.py
```

---

## 📁 File Overview

| File | Purpose |
|------|---------|
| `mapping_engine.py`   | Converts scenario names → test parameters |
| `automation_engine.py`| Playwright browser automation per feature |
| `assertion_engine.py` | Checks page HTML for PASS/FAIL signals |
| `defect_store.py`     | SQLite storage for all test results |
| `risk_engine.py`      | Calculates risk scores & release confidence |
| `test_runner.py`      | Orchestrates the full pipeline end-to-end |
| `dashboard.py`        | Streamlit UI — input, results, heatmap |
| `defects.db`          | Auto-created SQLite database |

---

## 🔁 Full Pipeline

```
Person-2 JSON output
  {"feature": "login", "tests": [...]}
         ↓
  mapping_engine.py   → get_params("login", "Valid login")
         ↓
  automation_engine.py → run_test(feature, params) → page HTML
         ↓
  assertion_engine.py  → assert_result(feature, html, expected)
         ↓
  defect_store.py      → store_result(...) → defects.db
         ↓
  risk_engine.py       → calculate_module_risk(feature)
         ↓
  dashboard.py         → display results + heatmap
```

---

## 🧪 Risk Formula

```
R = (Failure Rate × 0.5)
  + (Historical Defect Density × 0.3)
  + (Change Complexity × 0.2)

Release Confidence = (1 - R) × 100%
```

---

## 🤖 Playwright Assertion Signals

| Feature   | PASS signal              | FAIL signal              |
|-----------|--------------------------|--------------------------|
| login     | `Login Success`          | `Login Failed`           |
| signup    | `Account created for`    | `is required`, `mismatch`|
| search    | `product-card`, `result` | `cannot be empty`        |
| cart      | `cart-items`             | `empty`                  |
| checkout  | `Order Confirmed`        | `is required`            |
| contact   | `Message sent`           | `is required`            |

---

## 🔗 Integration with Person 2

Person 2 returns:
```json
{
  "feature": "login",
  "tests": ["Valid login", "Invalid password", "Empty email"]
}
```

Pass directly into `test_runner.run_test_suite()` or paste into the dashboard JSON input box.
