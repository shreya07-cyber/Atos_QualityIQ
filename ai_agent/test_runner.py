"""
test_runner.py
--------------
Orchestrates the full pipeline AND performs live cross-module
regression checks after every single test case.
"""

from mapping_engine    import get_params
from automation_engine import run_test
from assertion_engine  import assert_result
from defect_store      import store_result, get_best_run, get_latest_run
from risk_engine       import calculate_module_risk
from history_store     import store_run
from notifier          import build_notifications, build_regression_notifications


def _safe_params(params):
    if not params:
        return {}
    safe = dict(params)
    for key in ("password", "confirm_password"):
        if key in safe and safe[key]:
            safe[key] = "***"
    return safe


def check_regression_now(current_feature, log):
    """
    After each test case, re-run a quick spot-check on all OTHER modules
    that have previously passed scenarios, to detect cross-module regressions.

    Returns list of regression dicts.
    """
    from defect_store import get_module_summary
    from automation_engine import run_test as _run
    from assertion_engine  import assert_result as _assert

    summary = get_module_summary()
    regressions = []

    for module in summary:
        if module == current_feature:
            continue

        # Get best historical run for this module
        best_run = get_best_run(module)
        if not best_run:
            continue

        # Pick only scenarios that previously PASSED
        passing_scenarios = [r for r in best_run if r["result"] == "PASS"]
        if not passing_scenarios:
            continue

        # Re-test each previously-passing scenario
        for record in passing_scenarios:
            scenario = record["scenario"]
            params   = get_params(module, scenario)
            if params is None:
                continue

            log(f"   🔍 Regression check: [{module.upper()}] {scenario}")
            page_content  = _run(module, params)
            assertion     = _assert(module, page_content, params.get("expect", "pass"))
            current_result = assertion["result"]

            # Store the re-check result
            store_result(module, scenario, current_result,
                         assertion.get("reason", ""),
                         assertion.get("matched", ""))

            if current_result == "FAIL":
                regressions.append({
                    "affected_module": module,
                    "scenario":        scenario,
                    "reason":          assertion["reason"],
                    "was":             "PASS",
                    "now":             "FAIL",
                })
                log(f"   🔴 REGRESSION: [{module.upper()}] {scenario} was PASS → now FAIL")
            else:
                log(f"   ✅ Still passing: [{module.upper()}] {scenario}")

    return regressions


def run_test_suite(test_case: dict, callback=None) -> dict:
    feature   = test_case.get("feature", "unknown")
    scenarios = test_case.get("tests", [])

    def log(msg):
        if callback:
            callback(msg)
        else:
            print(msg)

    log(f"🚀 Starting suite: [{feature.upper()}]  ({len(scenarios)} scenarios)")

    results            = []
    all_regressions    = []   # collects every regression found across the run

    for i, scenario in enumerate(scenarios, 1):
        log(f"\n{'─'*48}")
        log(f"[{i}/{len(scenarios)}] Scenario: {scenario}")

        # STEP 1 — map
        params = get_params(feature, scenario)
        if params is None:
            log(f"   ⚠️  No mapping found — skipping.")
            results.append({
                "scenario": scenario, "result": "ERROR",
                "reason": "No mapping found", "matched": "none", "params": None,
            })
            store_result(feature, scenario, "ERROR", "No mapping found")
            continue

        expected = params.get("expect", "pass")
        log(f"   📋 Params: {_safe_params(params)}")

        # STEP 2 — automate
        log(f"   🌐 Running Playwright…")
        page_content = run_test(feature, params)

        # STEP 3 — assert
        assertion  = assert_result(feature, page_content, expected)
        result_str = assertion["result"]
        icon       = "✅" if result_str == "PASS" else ("❌" if result_str == "FAIL" else "⚠️")
        log(f"   {icon} {result_str} — {assertion['reason']}")

        # STEP 4 — store
        store_result(feature, scenario, result_str,
                     assertion.get("reason", ""), assertion.get("matched", ""))

        results.append({
            "scenario": scenario,
            "result":   result_str,
            "reason":   assertion["reason"],
            "matched":  assertion["matched"],
            "params":   _safe_params(params),
        })

        # STEP 5 — live cross-module regression check after EVERY test case
        log(f"\n   🔄 Checking all other modules for regressions…")
        regs = check_regression_now(feature, log)
        if regs:
            all_regressions.extend(regs)
            for reg in regs:
                log(f"   🚨 REGRESSION in [{reg['affected_module'].upper()}]: {reg['scenario']}")
        else:
            log(f"   ✅ All other modules still healthy.")

    # STEP 6 — final risk score
    risk   = calculate_module_risk(feature)
    passed = sum(1 for r in results if r["result"] == "PASS")
    failed = sum(1 for r in results if r["result"] == "FAIL")
    errors = sum(1 for r in results if r["result"] == "ERROR")

    log(f"\n{'═'*48}")
    log(f"📊 SUITE COMPLETE — {feature.upper()}")
    log(f"   ✅ Passed : {passed}")
    log(f"   ❌ Failed : {failed}")
    log(f"   ⚠️  Errors : {errors}")
    log(f"   Risk Score  : {risk['risk_score']}")
    log(f"   Confidence  : {risk['confidence_pct']}%")
    log(f"   Risk Level  : {risk['risk_label']}")
    if all_regressions:
        log(f"   🚨 Cross-module regressions found: {len(all_regressions)}")
    else:
        log(f"   ✅ No regressions detected in other modules.")
    log(f"{'═'*48}")

    # ── STEP 7: Save to history ──────────────────────────────────────────────
    story_id = test_case.get("story_id", "") or test_case.get("jira_key", "") or feature
    store_run(story_id, feature, results)

    # ── STEP 8: Build notifications ───────────────────────────────────────────
    assignee = test_case.get("assignee", "")
    notifs   = build_notifications(feature, results, story_id, assignee)
    notifs  += build_regression_notifications(all_regressions)

    return {
        "feature":       feature,
        "user_story":    test_case.get("user_story", ""),
        "story_id":      story_id,
        "jira_key":      test_case.get("jira_key", ""),
        "assignee":      assignee,
        "results":       results,
        "summary": {
            "total":   len(results),
            "passed":  passed,
            "failed":  failed,
            "errors":  errors,
        },
        "risk":          risk,
        "regressions":   all_regressions,
        "notifications": notifs,
    }