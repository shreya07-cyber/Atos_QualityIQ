"""
prioritizer.py
--------------
Risk-based test prioritization.

Formula:
  Risk Score = (Jira Priority Weight)
             + (Historical Failure Count × 2)
             + (Critical Feature Bonus)

Higher score = run first.
"""

from history_store import get_failure_count, get_feature_summary

# ── WEIGHTS ───────────────────────────────────────────────────────────────────
JIRA_PRIORITY_WEIGHT = {
    "Highest": 10,
    "High":     8,
    "Medium":   5,
    "Low":      2,
    "Lowest":   1,
    "Unknown":  3,
}

CRITICAL_FEATURES = {
    "checkout": 10,   # payment — most critical
    "login":     8,   # auth
    "cart":      6,
    "signup":    4,
    "search":    3,
    "contact":   1,
}


def score_story(feature: str, jira_priority: str = "Medium",
                story_id: str = "") -> dict:
    """
    Calculates a risk score for a story/feature.
    Returns a dict with the score and breakdown.
    """
    priority_w  = JIRA_PRIORITY_WEIGHT.get(jira_priority, 3)
    fail_count  = get_failure_count(feature)
    critical_w  = CRITICAL_FEATURES.get(feature.lower(), 2)

    score = priority_w + (fail_count * 2) + critical_w

    summary = get_feature_summary(feature)

    return {
        "story_id":        story_id or feature,
        "feature":         feature,
        "jira_priority":   jira_priority,
        "priority_weight": priority_w,
        "failure_count":   fail_count,
        "failure_bonus":   fail_count * 2,
        "critical_bonus":  critical_w,
        "risk_score":      score,
        "frequent_failure": summary["frequent"],
        "label":           _label(score),
    }


def _label(score: int) -> str:
    if score >= 20:
        return "🔴 Critical"
    elif score >= 12:
        return "🟠 High"
    elif score >= 7:
        return "🟡 Medium"
    else:
        return "🟢 Low"


def prioritize(stories: list) -> list:
    """
    stories = list of dicts:
      {"feature": "login", "jira_priority": "High", "story_id": "PDM-7", "tests": [...]}

    Returns stories sorted by risk score (highest first).
    Each story gets a "priority_info" key added.
    """
    scored = []
    for s in stories:
        info = score_story(
            s.get("feature", "general"),
            s.get("jira_priority", "Medium"),
            s.get("story_id", ""),
        )
        scored.append({**s, "priority_info": info})

    scored.sort(key=lambda x: x["priority_info"]["risk_score"], reverse=True)
    return scored


def adaptive_depth(feature: str, base_count: int = 6) -> int:
    """
    Returns how many test cases to generate based on failure history.
    More failures → more tests.

    Base:          6 tests
    3+ failures:   8 tests
    6+ failures:  10 tests
    """
    fails = get_failure_count(feature)
    if fails >= 6:
        return min(base_count + 4, 10)
    elif fails >= 3:
        return min(base_count + 2, 8)
    return base_count