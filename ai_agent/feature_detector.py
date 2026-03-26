"""
feature_detector.py
-------------------
Detects which e-commerce feature a user story refers to using keyword matching.
"""

FEATURE_KEYWORDS = {
    "login":    ["login", "sign in", "signin", "log in", "authenticate", "credentials"],
    "signup":   ["signup", "sign up", "register", "create account", "registration"],
    "checkout": ["checkout", "place order", "payment", "billing", "shipping address", "order"],
    "cart":     ["cart", "basket", "add to cart", "remove from cart"],
    "search":   ["search", "find product", "browse", "filter", "look for"],
    "contact":  ["contact", "message", "support", "enquiry", "help form", "feedback"],
}


def detect_feature(story: str) -> str:
    story_lower = story.lower()
    for feature, keywords in FEATURE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in story_lower:
                return feature
    return "general"


def detect_feature_with_confidence(story: str) -> dict:
    story_lower = story.lower()
    scores = {}
    for feature, keywords in FEATURE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in story_lower)
        if score > 0:
            scores[feature] = score

    if not scores:
        return {"feature": "general", "confidence": 0, "all_scores": {}}

    best    = max(scores, key=scores.get)
    conf    = round((scores[best] / len(FEATURE_KEYWORDS[best])) * 100, 1)
    return {"feature": best, "confidence": conf, "all_scores": scores}