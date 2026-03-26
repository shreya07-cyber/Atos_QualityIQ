"""
test_formatter.py
-----------------
Wraps feature + scenarios into the structured dict Person 3 expects.
"""

import json


def format_tests(feature: str, tests: list) -> dict:
    return {
        "feature": feature.lower().strip(),
        "tests":   [t.strip() for t in tests if t.strip()],
    }


def format_tests_with_meta(feature: str, tests: list, story: str) -> dict:
    return {
        "feature":    feature.lower().strip(),
        "tests":      [t.strip() for t in tests if t.strip()],
        "total":      len(tests),
        "user_story": story,
    }


def to_json(test_case: dict, indent: int = 2) -> str:
    return json.dumps(test_case, indent=indent)


def print_test_case(test_case: dict):
    print(f"\n{'─'*45}")
    print(f"  Feature : {test_case['feature'].upper()}")
    print(f"  Tests   : {len(test_case['tests'])}")
    print(f"{'─'*45}")
    for i, t in enumerate(test_case["tests"], 1):
        print(f"  {i:>2}. {t}")
    print(f"{'─'*45}\n")