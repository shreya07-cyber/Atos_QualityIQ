"""
jira_connector.py
-----------------
Fetches user stories directly from Jira and converts them
into the format Person 2's pipeline expects.

Setup:
  1. Fill in EMAIL, API_TOKEN, DOMAIN below
  2. pip install requests
  3. Use in dashboard — "Fetch from Jira" mode
"""

import requests
from requests.auth import HTTPBasicAuth

# ── CONFIGURE THESE ───────────────────────────────────────────────────────────
EMAIL = "write your mail"
API_TOKEN = "api key"
DOMAIN = "domain name"
# ─────────────────────────────────────────────────────────────────────────────


def _extract_text(description):
    """Converts Jira's Atlassian Document Format (ADF) to plain text."""
    if not description:
        return ""
    text = ""
    try:
        for block in description.get("content", []):
            if "content" in block:
                for item in block["content"]:
                    if item.get("type") == "text":
                        text += item["text"] + " "
    except Exception:
        return ""
    return text.strip()


def fetch_story(issue_key: str) -> dict:
    """
    Fetches a Jira issue and returns:
    {
        "issue_key":   "PDM-7",
        "summary":     "User should be able to login",
        "description": "Full description text...",
        "user_story":  "User should be able to login. Full description text...",
        "status":      "To Do",
        "priority":    "Medium",
    }

    Raises ValueError if credentials not set or request fails.
    """
    if not EMAIL or not API_TOKEN or not DOMAIN:
        raise ValueError(
            "Jira credentials not configured.\n"
            "Open jira_connector.py and fill in EMAIL, API_TOKEN, DOMAIN."
        )

    url      = f"https://{DOMAIN}/rest/api/3/issue/{issue_key}"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(EMAIL, API_TOKEN),
        headers={"Accept": "application/json"},
        timeout=10,
    )

    if response.status_code == 401:
        raise ValueError("Jira authentication failed — check your EMAIL and API_TOKEN.")
    if response.status_code == 404:
        raise ValueError(f"Issue '{issue_key}' not found — check the issue key and DOMAIN.")
    if response.status_code != 200:
        raise ValueError(f"Jira API error {response.status_code}: {response.text[:200]}")

    data        = response.json()
    fields      = data["fields"]
    summary     = fields.get("summary", "")
    description = _extract_text(fields.get("description", {}))
    status      = fields.get("status", {}).get("name", "Unknown")
    priority    = fields.get("priority", {}).get("name", "Unknown") if fields.get("priority") else "Unknown"

    # ── Extract assignee (developer assigned to this story) ───────────────────
    assignee_field = fields.get("assignee") or {}
    assignee_email = assignee_field.get("emailAddress", "")
    assignee_name  = assignee_field.get("displayName", "Unassigned")
    # ─────────────────────────────────────────────────────────────────────────

    # Combine summary + description into one user story string
    user_story = summary
    if description:
        user_story = f"{summary}. {description}"

    return {
        "issue_key":     issue_key.upper(),
        "summary":       summary,
        "description":   description,
        "user_story":    user_story,
        "status":        status,
        "priority":      priority,
        "assignee":      assignee_email,   # developer's email — used by notifier
        "assignee_name": assignee_name,    # developer's display name — shown in dashboard
    }


def fetch_multiple(issue_keys: list) -> list:
    """Fetches multiple issues. Skips failed ones with a warning."""
    results = []
    for key in issue_keys:
        try:
            results.append(fetch_story(key.strip()))
        except ValueError as e:
            results.append({
                "issue_key":  key.upper(),
                "error":      str(e),
                "user_story": "",
            })
    return results


def is_configured() -> bool:
    """Returns True if Jira credentials have been filled in."""
    return bool(EMAIL and API_TOKEN and DOMAIN)


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else "PDM-7"
    try:
        story = fetch_story(key)
        print(f"\n✅ Fetched: {story['issue_key']}")
        print(f"   Summary  : {story['summary']}")
        print(f"   Status   : {story['status']}")
        print(f"   Priority : {story['priority']}")
        print(f"   Story    : {story['user_story'][:200]}")
    except ValueError as e:
        print(f"❌ {e}")