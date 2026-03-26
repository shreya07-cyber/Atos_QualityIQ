"""

"""

import json
import time
import requests
from feature_detector import detect_feature

# ── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = "grok api key"      # ← paste your key from console.groq.com
GROQ_MODEL   = "model name"
GROQ_URL     = "url"


# ── RULE-BASED FALLBACK (used if API key not set or call fails) ───────────────
SCENARIO_BANK = {
    "login":    ["Valid login with correct credentials","Login with wrong password",
                 "Login with empty email field","Login with empty password field",
                 "Login with both fields empty","Login with SQL injection in email",],
    "signup":   ["Valid signup with all correct fields","Signup with mismatched passwords",
                 "Signup with password shorter than 6 characters","Signup with invalid email format",
                 "Signup with empty name field","Signup with all fields empty",],
    "search":   ["Valid search returns matching products","Empty search query shows error",
                 "Search with only special characters","Search for non-existent product",
                 "Search with very long query string","Partial word search returns results",],
    "cart":     ["Add single item to cart successfully","Add multiple items to cart",
                 "Remove item from cart","View empty cart page",
                 "Add same item twice increases quantity","Cart total updates correctly",],
    "checkout": ["Valid checkout with all correct fields","Checkout with empty address field",
                 "Checkout with invalid phone number","Checkout with empty name field",
                 "Checkout with cash on delivery","Order confirmation shown after success",],
    "contact":  ["Valid contact form submission","Submit with empty message field",
                 "Submit with invalid email address","Submit with empty name field",
                 "Submit with very long message over 2000 chars","Success message shown after submit",],
    "general":  ["Valid form submission with correct data","Submission with all fields empty",
                 "Submission with invalid email format","Submission with special characters",
                 "Submission with very long input","Error message shown on invalid input",],
}


def _build_messages(story: str) -> list:
    return [
        {
            "role": "system",
            "content": (
                "You are a senior QA engineer specialising in e-commerce web applications. "
                "When given a user story you output ONLY a valid JSON array of test scenario names. "
                "No explanation, no markdown, no code fences — just the raw JSON array of strings."
            )
        },
        {
            "role": "user",
            "content": f"""Generate 6 test scenario names for this user story.

Include: positive cases, negative cases, and edge cases.
Each scenario name should be short (5-8 words), specific, and automation-friendly.

Output format (raw JSON array of strings only):
["Scenario one here", "Scenario two here", ...]

User Story: {story}"""
        }
    ]


def _call_groq(story: str, retries: int = 2) -> list | None:
    """Calls Groq API. Returns list of scenario strings or None on failure."""
    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json"
    }
    payload = {
        "model":       GROQ_MODEL,
        "messages":    _build_messages(story),
        "max_tokens":  400,
        "temperature": 0.3,
        "stream":      False,
    }

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)

            if resp.status_code in (429, 503):
                wait = int(resp.headers.get("Retry-After", 20))
                time.sleep(min(wait + 5, 40))
                continue

            if resp.status_code != 200:
                return None

            content = resp.json()["choices"][0]["message"]["content"].strip()
            return _parse_json_array(content)

        except Exception:
            if attempt < retries:
                time.sleep(5)

    return None


def _parse_json_array(text: str) -> list | None:
    """Extracts a JSON array from model output, handling markdown fences."""
    if not text:
        return None

    # Strip markdown fences
    if "```" in text:
        for block in text.split("```"):
            block = block.strip()
            if block.lower().startswith("json"):
                block = block[4:].strip()
            if block.startswith("["):
                text = block
                break

    start = text.find("[")
    end   = text.rfind("]") + 1
    if start == -1 or end == 0:
        return None

    try:
        parsed = json.loads(text[start:end])
        # Accept list of strings OR list of dicts with "scenario" key
        if isinstance(parsed, list):
            result = []
            for item in parsed:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    result.append(item.get("scenario", str(item)))
            return result if result else None
    except json.JSONDecodeError:
        return None

    return None


def _rule_based(story: str) -> list:
    """Fallback: returns scenarios from rule bank based on detected feature."""
    feature = detect_feature(story)
    return SCENARIO_BANK.get(feature, SCENARIO_BANK["general"])


def generate_tests(story: str, count: int = 0) -> str:
    """
    Main function. Tries Groq API first, falls back to rule-based.
    count=0 means use adaptive depth based on failure history.
    Returns a numbered text string (same format as before).
    """
    # Adaptive depth — increase test count for historically failing features
    if count == 0:
        try:
            from prioritizer import adaptive_depth
            feature = detect_feature(story)
            count   = adaptive_depth(feature)
        except Exception:
            count = 6

    # Try AI first
    if GROQ_API_KEY and GROQ_API_KEY.strip():
        scenarios = _call_groq(story)
        if scenarios:
            lines = [f"{i+1}. {s}" for i, s in enumerate(scenarios[:count])]
            return "\n".join(lines)

    # Fallback — rule-based (always works, no network needed)
    time.sleep(0.5)
    scenarios = _rule_based(story)
    lines = [f"{i+1}. {s}" for i, s in enumerate(scenarios[:count])]
    return "\n".join(lines)


def generate_tests_with_retry(story: str, retries: int = 2) -> str:
    """Drop-in replacement — same interface as before."""
    return generate_tests(story)


def is_ai_enabled() -> bool:
    """Returns True if Groq API key is configured."""
    return bool(GROQ_API_KEY and GROQ_API_KEY.strip())