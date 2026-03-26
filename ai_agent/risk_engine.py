"""
risk_engine.py
--------------
Calculates risk scores per module using the formula:
  R = (Failure Rate × 0.5) + (Historical Defect Density × 0.3) + (Change Complexity × 0.2)

Release Confidence = (1 - R) × 100%
"""

from defect_store import get_module_summary, get_defect_density, detect_regression

# ── COMPLEXITY SCORES ──────────────────────────────────────────────────────────
# Subjective complexity per module (0.0 – 1.0).
# Higher = more complex code = more risk even without failures.
MODULE_COMPLEXITY = {
    "login":    0.3,
    "signup":   0.4,
    "search":   0.3,
    "cart":     0.6,
    "checkout": 0.8,
    "contact":  0.2,
}

# ── RISK THRESHOLDS ────────────────────────────────────────────────────────────
def risk_label(score: float) -> str:
    if score >= 0.65:
        return "🔴 High"
    elif score >= 0.35:
        return "🟡 Medium"
    else:
        return "🟢 Low"


def calculate_module_risk(module: str) -> dict:
    """
    Returns risk data for a single module:
    {
      module, failure_rate, defect_density, complexity,
      risk_score, confidence_pct, risk_label, regression
    }
    """
    summary = get_module_summary()
    mod_data = summary.get(module, {"passed": 0, "failed": 0, "errors": 0, "total": 0})

    total  = mod_data["total"]
    failed = mod_data["failed"]

    failure_rate     = (failed / total) if total > 0 else 0.0
    defect_density   = get_defect_density(module)
    complexity       = MODULE_COMPLEXITY.get(module, 0.5)
    regression       = detect_regression(module)

    risk_score = (
        failure_rate   * 0.5 +
        defect_density * 0.3 +
        complexity     * 0.2
    )
    risk_score = round(min(risk_score, 1.0), 4)
    confidence = round((1 - risk_score) * 100, 1)

    return {
        "module":          module,
        "total_tests":     total,
        "passed":          mod_data["passed"],
        "failed":          failed,
        "errors":          mod_data["errors"],
        "failure_rate":    round(failure_rate, 4),
        "defect_density":  round(defect_density, 4),
        "complexity":      complexity,
        "risk_score":      risk_score,
        "confidence_pct":  confidence,
        "risk_label":      risk_label(risk_score),
        "regression":      regression,
    }


def calculate_all_risks() -> dict:
    """Returns risk data for every module that has records in the DB."""
    summary = get_module_summary()
    results = {}
    for module in summary:
        results[module] = calculate_module_risk(module)
    return results


def overall_risk() -> dict:
    """
    Aggregates across all modules into one overall release risk score.
    """
    all_risks = calculate_all_risks()
    if not all_risks:
        return {
            "risk_score":     0.0,
            "confidence_pct": 100.0,
            "risk_label":     "🟢 Low",
            "modules_tested": 0,
        }

    avg_score = sum(v["risk_score"] for v in all_risks.values()) / len(all_risks)
    avg_score = round(avg_score, 4)
    confidence = round((1 - avg_score) * 100, 1)

    regressions = [m for m, v in all_risks.items() if v["regression"]]

    return {
        "risk_score":     avg_score,
        "confidence_pct": confidence,
        "risk_label":     risk_label(avg_score),
        "modules_tested": len(all_risks),
        "regressions":    regressions,
        "per_module":     all_risks,
    }
