"""
assertion_engine.py
-------------------
Checks raw page HTML content against expected pass/fail signals per feature.
Returns "PASS", "FAIL", or "ERROR".
"""

# ── PASS SIGNALS per feature ───────────────────────────────────────────────────
PASS_SIGNALS = {
    "login":    ["Login Success"],
    "signup":   ["Account created for", "Welcome aboard"],
    "search":   ["result", "product-card"],          # found results
    "cart":     ["cart-items", "Your Cart", "added to cart"],
    "checkout": ["Order Confirmed", "order-success"],
    "contact":  ["Message sent", "get back to you"],
}

# ── FAIL SIGNALS per feature ───────────────────────────────────────────────────
FAIL_SIGNALS = {
    "login":    ["Login Failed", "is required", "invalid", "valid email"],
    "signup":   ["is required", "do not match", "at least 6", "valid email"],
    "search":   ["cannot be empty", "regular characters"],
    "cart":     ["empty", "not found"],
    "checkout": ["is required", "valid phone", "valid email"],
    "contact":  ["is required", "valid email", "cannot be empty", "too long"],
}

# ── EMPTY / NO-RESULTS SIGNALS ─────────────────────────────────────────────────
EMPTY_SIGNALS = {
    "search":   ["No results found", "no-results", "couldn't find"],
    "cart":     ["Your cart is empty", "empty-cart"],
}


def assert_result(feature: str, page_content: str, expected: str = "pass") -> dict:
    """
    Checks page_content for signals and returns a result dict:
      {
        "result":  "PASS" | "FAIL" | "ERROR",
        "reason":  str,
        "matched": str   # which signal triggered
      }
    """
    feature = feature.lower()
    content = page_content.lower()

    if "<timeout/>" in page_content:
        return {"result": "ERROR", "reason": "Page timed out", "matched": "timeout"}

    if "<connection_refused/>" in page_content:
        return {"result": "ERROR", "reason": "Flask app not reachable — server may have failed to start", "matched": "connection_refused"}

    if "<unsupported_feature/>" in page_content:
        return {"result": "ERROR", "reason": "Feature not supported", "matched": "none"}

    # Check empty/no-results signals
    empty_sigs = EMPTY_SIGNALS.get(feature, [])
    for sig in empty_sigs:
        if sig.lower() in content:
            if expected == "empty":
                return {"result": "PASS", "reason": "Empty/no-results as expected", "matched": sig}
            elif expected == "pass":
                return {"result": "FAIL", "reason": "Expected results but got empty", "matched": sig}

    # Check PASS signals
    pass_sigs = PASS_SIGNALS.get(feature, [])
    for sig in pass_sigs:
        if sig.lower() in content:
            if expected in ("pass", "empty"):
                return {"result": "PASS", "reason": "Success signal found", "matched": sig}
            else:
                # Expected fail but got pass
                return {"result": "FAIL", "reason": "Expected failure but test passed", "matched": sig}

    # Check FAIL signals
    fail_sigs = FAIL_SIGNALS.get(feature, [])
    for sig in fail_sigs:
        if sig.lower() in content:
            if expected == "fail":
                return {"result": "PASS", "reason": "Error correctly shown", "matched": sig}
            else:
                return {"result": "FAIL", "reason": f"Unexpected error: '{sig}'", "matched": sig}

    # No signal found at all
    return {
        "result": "ERROR",
        "reason": "No recognizable signal found in page",
        "matched": "none"
    }


def bulk_assert(feature: str, results: list) -> list:
    """
    results: list of {"scenario", "page_content", "expected"}
    Returns list of {"scenario", "result", "reason", "matched"}
    """
    output = []
    for r in results:
        assertion = assert_result(feature, r["page_content"], r.get("expected", "pass"))
        output.append({
            "scenario": r["scenario"],
            **assertion
        })
    return output