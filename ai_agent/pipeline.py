"""
pipeline.py
-----------
Person 2's main entry point. No API key required.

Usage:
    python pipeline.py
    python pipeline.py User should be able to login
"""

import sys
import os

from test_generator   import generate_tests_with_retry
from scenario_parser  import parse_and_deduplicate
from feature_detector import detect_feature, detect_feature_with_confidence
from test_formatter   import format_tests_with_meta, print_test_case, to_json


def get_test_cases(user_story: str) -> dict:
    """
    Main pipeline — takes a user story, returns structured test cases.

    Return format:
    {
        "feature":    "login",
        "tests":      ["Valid login with correct credentials", ...],
        "total":      6,
        "user_story": "User should be able to login"
    }
    """
    print(f"\n🔍 Detecting feature...")
    detection  = detect_feature_with_confidence(user_story)
    feature    = detection["feature"]
    confidence = detection["confidence"]
    print(f"   Feature   : {feature.upper()}")
    print(f"   Confidence: {confidence}%")

    print(f"\n🤖 Generating test scenarios...")
    raw_text = generate_tests_with_retry(user_story)

    print(f"\n📋 Parsing scenarios...")
    tests = parse_and_deduplicate(raw_text)
    print(f"   Parsed {len(tests)} scenarios")

    result = format_tests_with_meta(feature, tests, user_story)
    print_test_case(result)
    return result


def get_test_cases_silent(user_story: str) -> dict:
    """Same as get_test_cases but no console output — used by dashboard."""
    feature  = detect_feature(user_story)
    raw_text = generate_tests_with_retry(user_story)
    tests    = parse_and_deduplicate(raw_text)
    return format_tests_with_meta(feature, tests, user_story)


# ── CLI ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        story = " ".join(sys.argv[1:])
    else:
        print("=" * 50)
        print("  Person 2 — AI Test Case Generator (offline)")
        print("=" * 50)
        story = input("\nEnter user story: ").strip()
        if not story:
            story = "User should be able to login with email and password"
            print(f"Using default: {story}")

    result = get_test_cases(story)

    print("📦 JSON output for Person 3:")
    print(to_json(result))