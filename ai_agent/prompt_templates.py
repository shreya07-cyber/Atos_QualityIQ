"""
prompt_templates.py
-------------------
Kept for module compatibility.
In the rule-based version, prompts are not sent to any API —
they are just used as display text to simulate the AI prompt step.
"""


def create_prompt(story: str) -> str:
    return (
        f"You are a QA automation expert.\n"
        f"Generate functional, negative, and edge-case test scenarios "
        f"for this e-commerce feature:\n\n{story}\n\nReturn them as a numbered list."
    )


def create_feature_prompt(story: str, feature: str) -> str:
    return (
        f"You are a QA automation expert specialising in {feature}.\n"
        f"Generate test scenarios for: {story}\n\nReturn them as a numbered list."
    )