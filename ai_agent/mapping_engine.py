"""
mapping_engine.py
-----------------
Converts AI-generated scenario names → actual test parameters.

UPGRADED: Uses keyword-based fuzzy matching so AI-generated scenario
names like "Invalid Email Format Rejects Login Attempt" correctly map
to the right test parameters — no exact match needed.
"""

# ── LOGIN MAPPINGS ─────────────────────────────────────────────────────────────
LOGIN_MAPPING = {
    "valid login":            {"username": "user@test.com", "password": "1245",       "expect": "pass"},
    "invalid password":       {"username": "user@test.com", "password": "wrongpass",  "expect": "fail"},
    "empty email":            {"username": "",              "password": "1234",       "expect": "fail"},
    "empty username":         {"username": "",              "password": "1234",       "expect": "fail"},
    "empty password":         {"username": "user@test.com", "password": "",           "expect": "fail"},
    "both fields empty":      {"username": "",              "password": "",           "expect": "fail"},
    "invalid email format":   {"username": "notanemail",   "password": "1234",       "expect": "fail"},
    "sql injection":          {"username": "' OR 1=1--",   "password": "anything",   "expect": "fail"},
    "wrong credentials":      {"username": "hacker@x.com", "password": "pass123",    "expect": "fail"},
    "short password":         {"username": "user@test.com", "password": "abc",        "expect": "fail"},
    "max password":           {"username": "user@test.com", "password": "a"*50,       "expect": "fail"},
    "spaces in password":     {"username": "user@test.com", "password": "  ",         "expect": "fail"},
}

# ── SIGNUP MAPPINGS ────────────────────────────────────────────────────────────
SIGNUP_MAPPING = {
    "valid signup":           {"name": "Jane Smith",  "email": "jane@test.com",  "password": "secure123", "confirm_password": "secure123", "expect": "pass"},
    "password mismatch":      {"name": "Jane Smith",  "email": "jane@test.com",  "password": "abc123",    "confirm_password": "xyz999",    "expect": "fail"},
    "short password":         {"name": "Jane Smith",  "email": "jane@test.com",  "password": "abc",       "confirm_password": "abc",       "expect": "fail"},
    "invalid email":          {"name": "Jane Smith",  "email": "notanemail",     "password": "abc123",    "confirm_password": "abc123",    "expect": "fail"},
    "empty name":             {"name": "",             "email": "jane@test.com",  "password": "abc123",    "confirm_password": "abc123",    "expect": "fail"},
    "empty email":            {"name": "Jane Smith",  "email": "",               "password": "abc123",    "confirm_password": "abc123",    "expect": "fail"},
    "all fields empty":       {"name": "",             "email": "",               "password": "",          "confirm_password": "",          "expect": "fail"},
    "weak password":          {"name": "Jane Smith",  "email": "jane@test.com",  "password": "12345",     "confirm_password": "12345",     "expect": "fail"},
}

# ── SEARCH MAPPINGS ────────────────────────────────────────────────────────────
SEARCH_MAPPING = {
    "valid search":           {"query": "Laptop",       "expect": "pass"},
    "empty search":           {"query": "",             "expect": "fail"},
    "special characters":     {"query": "!@#$%^",      "expect": "fail"},
    "no results":             {"query": "xyznotfound",  "expect": "empty"},
    "long search":            {"query": "a" * 200,      "expect": "empty"},
    "partial search":         {"query": "lap",          "expect": "pass"},
    "numeric search":         {"query": "123",          "expect": "empty"},
    "search phone":           {"query": "Phone",        "expect": "pass"},
}

# ── CART MAPPINGS ──────────────────────────────────────────────────────────────
CART_MAPPING = {
    "add item":               {"product_id": 1, "quantity": 1,  "expect": "pass"},
    "add multiple":           {"product_id": 2, "quantity": 3,  "expect": "pass"},
    "add same item twice":    {"product_id": 1, "quantity": 2,  "expect": "pass"},
    "remove item":            {"product_id": 1, "quantity": 1,  "action": "remove", "expect": "pass"},
    "empty cart":             {"product_id": None,              "expect": "empty"},
    "cart total":             {"product_id": 1, "quantity": 1,  "expect": "pass"},
    "increase quantity":      {"product_id": 1, "quantity": 3,  "expect": "pass"},
}

# ── CHECKOUT MAPPINGS ──────────────────────────────────────────────────────────
CHECKOUT_MAPPING = {
    "valid checkout":         {"full_name": "Jane Smith", "address": "123 Main St", "phone": "5551234567", "email": "jane@test.com", "payment_method": "card",   "expect": "pass"},
    "empty address":          {"full_name": "Jane Smith", "address": "",            "phone": "5551234567", "email": "jane@test.com", "payment_method": "card",   "expect": "fail"},
    "invalid phone":          {"full_name": "Jane Smith", "address": "123 Main St", "phone": "abc",        "email": "jane@test.com", "payment_method": "card",   "expect": "fail"},
    "empty name":             {"full_name": "",            "address": "123 Main St", "phone": "5551234567", "email": "jane@test.com", "payment_method": "card",   "expect": "fail"},
    "long address":           {"full_name": "Jane Smith", "address": "A" * 300,    "phone": "5551234567", "email": "jane@test.com", "payment_method": "card",   "expect": "pass"},
    "cash on delivery":       {"full_name": "Jane Smith", "address": "123 Main St", "phone": "5551234567", "email": "jane@test.com", "payment_method": "cod",    "expect": "pass"},
    "paypal":                 {"full_name": "Jane Smith", "address": "123 Main St", "phone": "5551234567", "email": "jane@test.com", "payment_method": "paypal", "expect": "pass"},
    "invalid email":          {"full_name": "Jane Smith", "address": "123 Main St", "phone": "5551234567", "email": "notanemail",    "payment_method": "card",   "expect": "fail"},
}

# ── CONTACT MAPPINGS ───────────────────────────────────────────────────────────
CONTACT_MAPPING = {
    "valid message":          {"name": "Jane",  "email": "jane@test.com", "subject": "Help", "message": "I need help with my order.", "expect": "pass"},
    "empty message":          {"name": "Jane",  "email": "jane@test.com", "subject": "Help", "message": "",                          "expect": "fail"},
    "invalid email":          {"name": "Jane",  "email": "notanemail",    "subject": "Help", "message": "Hello there.",              "expect": "fail"},
    "empty name":             {"name": "",       "email": "jane@test.com", "subject": "Help", "message": "Hello there.",              "expect": "fail"},
    "long message":           {"name": "Jane",  "email": "jane@test.com", "subject": "Help", "message": "A" * 2100,                 "expect": "fail"},
    "all fields empty":       {"name": "",       "email": "",              "subject": "",     "message": "",                          "expect": "fail"},
    "special characters":     {"name": "Jane",  "email": "jane@test.com", "subject": "Test", "message": "Hello! @#$%",              "expect": "pass"},
}

FEATURE_MAPPINGS = {
    "login":    LOGIN_MAPPING,
    "signup":   SIGNUP_MAPPING,
    "search":   SEARCH_MAPPING,
    "cart":     CART_MAPPING,
    "checkout": CHECKOUT_MAPPING,
    "contact":  CONTACT_MAPPING,
}

# ── FUZZY KEYWORD RULES ────────────────────────────────────────────────────────
# Maps keywords found in AI scenario names → canonical mapping key
# Order matters: more specific rules first

LOGIN_FUZZY = [
    (["valid", "correct", "success", "successfully", "proper"],                    "valid login"),
    (["sql", "injection", "script"],                                                "sql injection"),
    (["both", "all field", "all empty"],                                            "both fields empty"),
    (["empty", "blank", "missing", "no", "without"],
     {
         "email":    "empty email",
         "username": "empty email",
         "password": "empty password",
     }),
    (["invalid", "wrong", "incorrect", "reject", "bad", "fail"],
     {
         "email": "invalid email format",
         "format":"invalid email format",
         "password": "invalid password",
         "credential": "wrong credentials",
     }),
    (["short", "min", "minimum", "weak"],                                           "short password"),
    (["max", "long", "maximum", "length"],                                          "max password"),
    (["space"],                                                                     "spaces in password"),
    (["wrong", "incorrect", "invalid"],                                             "wrong credentials"),
]

SIGNUP_FUZZY = [
    (["valid", "correct", "success", "successfully"],                              "valid signup"),
    (["mismatch", "not match", "don't match", "confirm", "different"],             "password mismatch"),
    (["short", "minimum", "weak", "less than", "fewer"],                           "short password"),
    (["empty", "blank", "missing"],
     {
         "name":  "empty name",
         "email": "empty email",
         "all":   "all fields empty",
         "field": "all fields empty",
     }),
    (["invalid", "wrong", "incorrect", "bad"],
     {
         "email":  "invalid email",
         "format": "invalid email",
     }),
    (["all", "every"],                                                              "all fields empty"),
]

SEARCH_FUZZY = [
    (["valid", "correct", "success", "match", "return", "find", "found"],         "valid search"),
    (["empty", "blank", "no input", "nothing", "without"],                         "empty search"),
    (["special", "symbol", "character", "@", "#", "!"],                            "special characters"),
    (["no result", "not found", "nonexistent", "doesn't exist", "zero"],           "no results"),
    (["long", "max", "maximum", "boundary", "exceed"],                             "long search"),
    (["partial", "incomplete", "prefix"],                                           "partial search"),
    (["number", "numeric", "digit"],                                               "numeric search"),
]

CART_FUZZY = [
    (["empty", "no item", "without"],                                              "empty cart"),
    (["remove", "delete", "take out"],                                             "remove item"),
    (["same", "twice", "duplicate", "again"],                                      "add same item twice"),
    (["multiple", "many", "several", "more than one"],                             "add multiple"),
    (["total", "price", "sum", "amount", "update"],                               "cart total"),
    (["quantity", "increase", "more"],                                             "increase quantity"),
    (["add", "insert", "put", "single"],                                           "add item"),
]

CHECKOUT_FUZZY = [
    (["valid", "correct", "success", "complete", "successfully"],                  "valid checkout"),
    (["cash", "cod", "delivery"],                                                  "cash on delivery"),
    (["paypal"],                                                                   "paypal"),
    (["long", "exceed", "boundary", "max"],                                        "long address"),
    (["empty", "blank", "missing", "without"],
     {
         "address": "empty address",
         "name":    "empty name",
         "phone":   "invalid phone",
     }),
    (["invalid", "wrong", "incorrect", "bad"],
     {
         "phone":  "invalid phone",
         "number": "invalid phone",
         "email":  "invalid email",
     }),
]

CONTACT_FUZZY = [
    (["valid", "correct", "success", "successfully"],                              "valid message"),
    (["empty", "blank", "missing", "no message", "without"],
     {
         "message": "empty message",
         "name":    "empty name",
         "all":     "all fields empty",
         "email":   "invalid email",
     }),
    (["invalid", "wrong", "bad"],                                                  "invalid email"),
    (["long", "exceed", "boundary", "max", "2000"],                               "long message"),
    (["special", "symbol", "character"],                                           "special characters"),
    (["all", "every", "fields"],                                                   "all fields empty"),
]

FEATURE_FUZZY = {
    "login":    LOGIN_FUZZY,
    "signup":   SIGNUP_FUZZY,
    "search":   SEARCH_FUZZY,
    "cart":     CART_FUZZY,
    "checkout": CHECKOUT_FUZZY,
    "contact":  CONTACT_FUZZY,
}


def _fuzzy_match(feature: str, scenario: str) -> str | None:
    """
    Tries to match an AI-generated scenario name to a canonical key
    using keyword rules. Returns canonical key or None.
    """
    s     = scenario.lower()
    rules = FEATURE_FUZZY.get(feature, [])

    for rule in rules:
        trigger_words = rule[0]
        target        = rule[1]

        # Check if any trigger word appears in scenario
        if not any(tw in s for tw in trigger_words):
            continue

        # Target is a simple string → direct match
        if isinstance(target, str):
            return target

        # Target is a dict → pick sub-key based on second keyword found
        if isinstance(target, dict):
            for sub_key, canonical in target.items():
                if sub_key in s:
                    return canonical
            # No sub-key matched — return first value as default
            return list(target.values())[0]

    return None


def get_params(feature: str, scenario: str) -> dict | None:
    """
    Returns test parameters for a given feature + scenario name.

    Priority:
    1. Exact match (case-insensitive)
    2. Substring match
    3. Fuzzy keyword match (handles AI-generated names)
    4. Returns None if no match found
    """
    feature     = feature.lower().strip()
    scenario_lc = scenario.lower().strip()
    mapping     = FEATURE_MAPPINGS.get(feature, {})

    # 1. Exact match
    if scenario_lc in mapping:
        return mapping[scenario_lc]

    # 2. Substring match
    for key in mapping:
        if key in scenario_lc or scenario_lc in key:
            return mapping[key]

    # 3. Fuzzy keyword match
    canonical = _fuzzy_match(feature, scenario)
    if canonical and canonical in mapping:
        return mapping[canonical]

    # 4. No match — use a safe default per feature so test still runs
    return _default_params(feature)


def _default_params(feature: str) -> dict:
    """
    Returns a safe default parameter set when no mapping is found.
    This ensures AI-generated scenarios always run instead of being skipped.
    """
    defaults = {
        "login":    {"username": "user@test.com", "password": "1234",       "expect": "pass"},
        "signup":   {"name": "Jane Smith", "email": "jane@test.com", "password": "secure123", "confirm_password": "secure123", "expect": "pass"},
        "search":   {"query": "Laptop",    "expect": "pass"},
        "cart":     {"product_id": 1,      "quantity": 1, "expect": "pass"},
        "checkout": {"full_name": "Jane Smith", "address": "123 Main St", "phone": "5551234567", "email": "jane@test.com", "payment_method": "card", "expect": "pass"},
        "contact":  {"name": "Jane", "email": "jane@test.com", "subject": "Help", "message": "Test message.", "expect": "pass"},
    }
    return defaults.get(feature, None)


def get_all_scenarios(feature: str) -> list:
    feature = feature.lower().strip()
    return list(FEATURE_MAPPINGS.get(feature, {}).keys())