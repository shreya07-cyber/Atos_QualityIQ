"""
scenario_parser.py
------------------
Converts raw numbered text into a clean Python list of scenario names.
"""

import re


def parse_scenarios(text: str) -> list:
    lines  = text.strip().split("\n")
    result = []
    for line in lines:
        line    = line.strip()
        if not line:
            continue
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)   # remove "1. " or "1) "
        cleaned = re.sub(r"^[-\*•]\s*", "", cleaned)    # remove "- " or "* "
        cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)  # remove **bold**
        cleaned = cleaned.rstrip(":").strip()
        if len(cleaned) >= 4:
            result.append(cleaned)
    return result


def parse_and_deduplicate(text: str) -> list:
    scenarios = parse_scenarios(text)
    seen, unique = set(), []
    for s in scenarios:
        key = s.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique