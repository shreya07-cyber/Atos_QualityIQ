"""
notifier.py
-----------
In-dashboard notification system + real email alerts to developers.

When test cases fail, the developer assigned in Jira gets an email
listing every failed scenario, the reason, and the story ID.

ONE-TIME GMAIL SETUP:
  1. Go to https://myaccount.google.com/apppasswords  (needs 2FA enabled)
  2. Create an App Password — name it "ATOS Notifier"
  3. Fill in SENDER_EMAIL and SENDER_APP_PASSWORD below
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── CONFIGURE THESE ───────────────────────────────────────────────────────────
SENDER_EMAIL        = "rutuja11199150@gmail.com"   # Gmail you send FROM
SENDER_APP_PASSWORD = "qsnb gkvt xrqg sfjd"    # App Password (not your login password)
# ─────────────────────────────────────────────────────────────────────────────


def _send_email(to_email: str, subject: str, body: str):
    """Sends email via Gmail SMTP. Silent no-op if credentials not set."""
    if not SENDER_EMAIL or SENDER_EMAIL == "your_gmail@gmail.com":
        return
    if not to_email or "@" not in to_email:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = to_email
        msg.attach(MIMEText(body, "plain"))
        html = body.replace("\n", "<br>")
        msg.attach(MIMEText(
            f"<html><body style='font-family:sans-serif;line-height:1.6'>{html}</body></html>",
            "html"
        ))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            s.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"[notifier] ✅ Email sent to {to_email}")
    except Exception as e:
        print(f"[notifier] ⚠️  Email to {to_email} failed: {e}")


def _send_failure_email(to_email, story_id, feature, failures, timestamp):
    """Sends one summary email listing all failed/error scenarios."""
    count   = len(failures)
    subject = f"⚠️ {count} test(s) failed — {story_id or feature.upper()} [{feature}]"
    lines   = [
        f"Hi,",
        f"",
        f"The following test case(s) FAILED for story {story_id or feature.upper()} "
        f"({feature} module) during the automated run at {timestamp}:",
        f"",
    ]
    for i, r in enumerate(failures, 1):
        lines.append(f"  {i}. Scenario : {r['scenario']}")
        lines.append(f"     Result   : {r['result']}")
        lines.append(f"     Reason   : {r.get('reason','Unknown')}")
        lines.append("")
    lines += [
        "Please review and fix the issues above.",
        "",
        "— ATOS Automated Test Platform",
    ]
    _send_email(to_email, subject, "\n".join(lines))


def build_notifications(feature: str, results: list,
                        story_id: str = "", assignee: str = "") -> list:
    """
    Builds dashboard notification dicts for FAIL/ERROR results
    and sends a real email to the assigned developer.
    """
    notifications = []
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M")
    failures = [r for r in results if r["result"] in ("FAIL", "ERROR")]

    for r in failures:
        level = "error" if r["result"] == "FAIL" else "warning"
        msg   = _build_message(story_id, feature, r["scenario"],
                               r.get("reason", ""), assignee)
        notifications.append({
            "level":    level,
            "story_id": story_id or feature.upper(),
            "feature":  feature,
            "scenario": r["scenario"],
            "reason":   r.get("reason", ""),
            "assignee": assignee or "Unassigned",
            "message":  msg,
            "time":     ts,
        })

    # Send ONE summary email to the developer covering all failures
    if failures and assignee and "@" in assignee:
        _send_failure_email(assignee, story_id, feature, failures, ts)

    return notifications


def _build_message(story_id, feature, scenario, reason, assignee) -> str:
    base = f"Test failed for **{story_id or feature.upper()}** → _{scenario}_"
    if reason:
        base += f"  \nReason: {reason}"
    if assignee and assignee != "Unassigned":
        base += f"  \nAssigned to: **{assignee}**"
    return base


def build_regression_notifications(regressions: list) -> list:
    notifications = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    for reg in regressions:
        notifications.append({
            "level":    "error",
            "story_id": reg["affected_module"].upper(),
            "feature":  reg["affected_module"],
            "scenario": reg["scenario"],
            "reason":   reg.get("reason", ""),
            "assignee": "Unassigned",
            "message":  (
                f"🔴 Regression in **{reg['affected_module'].upper()}** → "
                f"_{reg['scenario']}_ was PASS, now FAIL.\n"
                f"Reason: {reg.get('reason','')}"
            ),
            "time":     ts,
        })
    return notifications


def store_notifications(new_notifs: list):
    import streamlit as st
    existing = st.session_state.get("notifications", [])
    st.session_state["notifications"] = new_notifs + existing


def get_notifications() -> list:
    import streamlit as st
    return st.session_state.get("notifications", [])


def clear_notifications():
    import streamlit as st
    st.session_state["notifications"] = []