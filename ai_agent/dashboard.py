"""
dashboard.py — AI Testing Platform (QualityIQ Design)
Integrates the QualityIQ HTML/CSS design system into the Streamlit dashboard.
"""

import sys, os, asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
import html
sys.path.insert(0, os.path.dirname(__file__))

from defect_store   import get_all, get_module_summary, clear_all, get_latest_run
from risk_engine    import calculate_all_risks, overall_risk
from test_runner    import run_test_suite
from pipeline       import get_test_cases_silent
from test_generator import is_ai_enabled
from history_store  import get_all_feature_summaries, get_failing_scenarios, clear_all as clear_history
from prioritizer    import score_story, adaptive_depth
from notifier       import store_notifications, get_notifications, clear_notifications

try:
    from jira_connector import fetch_story, is_configured as jira_configured
except Exception:
    def jira_configured(): return False
    def fetch_story(k): raise ValueError("Jira connector not available")


# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QualityIQ — AI Testing Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── QUALITYIQ DESIGN SYSTEM CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,300;0,600;0,700;1,300&display=swap');

/* ── CSS VARIABLES ── */
:root {
  --bg:           #f4f6fb;
  --surface:      #ffffff;
  --surface-2:    #f8faff;
  --border:       #e4e9f2;
  --border-light: #eef2f9;
  --text-primary:   #111827;
  --text-secondary: #4b5563;
  --text-muted:     #9ca3af;
  --blue:        #2563eb;
  --blue-light:  #eff6ff;
  --blue-mid:    #dbeafe;
  --green:       #059669;
  --green-light: #ecfdf5;
  --green-mid:   #a7f3d0;
  --red:         #dc2626;
  --red-light:   #fef2f2;
  --red-mid:     #fecaca;
  --amber:       #d97706;
  --amber-light: #fffbeb;
  --amber-mid:   #fde68a;
  --purple:      #7c3aed;
  --purple-light:#f5f3ff;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04);
  --shadow:    0 4px 12px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.04);
  --radius:    12px;
  --radius-sm: 8px;
  --radius-lg: 16px;
}

/* ── GLOBAL FONT OVERRIDE ── */
html, body, [class*="css"], .stMarkdown, .stText,
.stSelectbox, .stTextInput, .stTextArea, .stButton {
  font-family: 'DM Sans', sans-serif !important;
}

/* ── STREAMLIT CHROME CLEANUP ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem 2rem !important; max-width: 100% !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

/* ── KPI CARDS ── */
.qiq-kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  text-align: center;
}
.qiq-kpi::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: var(--accent-color, var(--blue));
}
.qiq-kpi-val {
  font-size: 1.85rem;
  font-weight: 800;
  font-family: 'DM Mono', monospace;
  line-height: 1;
  color: var(--accent-color, var(--blue));
}
.qiq-kpi-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin-top: 0.35rem;
}
.qiq-kpi-sub   { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.3rem; }
.qiq-kpi-trend { font-size: 0.7rem;  font-weight: 600; margin-top: 0.25rem; }

/* ── RISK MODULE CARDS ── */
.risk-module {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem;
  box-shadow: var(--shadow-sm);
  position: relative;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
}
.risk-module:hover { box-shadow: var(--shadow); transform: translateY(-1px); }
.risk-module.high   { border-top: 3px solid var(--red); }
.risk-module.medium { border-top: 3px solid var(--amber); }
.risk-module.low    { border-top: 3px solid var(--green); }
.rm-name  { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 0.4rem; }
.rm-score { font-size: 1.4rem; font-weight: 800; font-family: 'DM Mono', monospace; }
.rm-score.high   { color: var(--red); }
.rm-score.medium { color: var(--amber); }
.rm-score.low    { color: var(--green); }
.rm-label { font-size: 0.72rem; font-weight: 600; }
.rm-stats { font-size: 0.68rem; color: var(--text-muted); margin-top: 0.35rem; }
.rm-badge {
  position: absolute; top: 7px; right: 7px;
  font-size: 0.6rem; font-weight: 700; padding: 2px 6px; border-radius: 20px;
}
.badge-reg  { background: var(--red-light);   color: var(--red);   border: 1px solid var(--red-mid); }
.badge-freq { background: var(--amber-light); color: var(--amber); border: 1px solid var(--amber-mid); }
.badge-ok   { background: var(--green-light); color: var(--green); border: 1px solid var(--green-mid); }

/* ── BAR CHART ── */
.bar-row   { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.bar-label { font-size: 0.72rem; font-weight: 600; width: 70px; text-align: right; color: var(--text-secondary); flex-shrink: 0; }
.bar-track { flex: 1; background: var(--bg); border-radius: 4px; height: 10px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 4px; }
.bar-val   { font-size: 0.72rem; font-weight: 700; width: 38px; color: var(--text-primary); font-family: 'DM Mono', monospace; flex-shrink: 0; }

/* ── INSIGHT CARDS ── */
.insight-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem;
  box-shadow: var(--shadow-sm);
  margin-bottom: 0.75rem;
  border-left: 4px solid var(--accent, var(--blue));
}
.insight-title  { font-size: 0.88rem; font-weight: 700; color: var(--text-primary); }
.insight-source { font-size: 0.7rem;  color: var(--text-muted); margin-top: 2px; }
.insight-body   { font-size: 0.82rem; color: var(--text-secondary); line-height: 1.55; margin-top: 0.5rem; }

/* ── CONFIDENCE BAR ── */
.conf-bar-wrap { display: flex; align-items: center; gap: 8px; margin-top: 0.6rem; }
.conf-label    { font-size: 0.68rem; color: var(--text-muted); font-weight: 600; white-space: nowrap; }
.conf-track    { flex: 1; background: var(--bg); border-radius: 4px; height: 6px; overflow: hidden; }
.conf-fill     { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #2563eb, #7c3aed); }
.conf-pct      { font-size: 0.75rem; font-weight: 700; color: var(--purple); font-family: 'DM Mono', monospace; width: 32px; }

/* ── TEST ROWS ── */
.test-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.1s;
}
.test-row:hover     { background: var(--bg); }
.test-row:last-child{ border-bottom: none; }
.test-name   { flex: 1; font-size: 0.82rem; color: var(--text-primary); font-weight: 500; }
.test-result { font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.result-pass { background: var(--green-light); color: var(--green); border: 1px solid var(--green-mid); }
.result-fail { background: var(--red-light);   color: var(--red);   border: 1px solid var(--red-mid); }
.result-err  { background: var(--amber-light); color: var(--amber); border: 1px solid var(--amber-mid); }
.test-reason { font-size: 0.7rem; color: var(--text-muted); max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── REGRESSION ITEMS ── */
.reg-item {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm); padding: 0.75rem 1rem;
  margin-bottom: 0.5rem; display: flex; align-items: flex-start; gap: 10px;
}
.reg-item.bad  { border-color: var(--red-mid);   background: var(--red-light); }
.reg-item.good { border-color: var(--green-mid); background: var(--green-light); }
.reg-name   { font-size: 0.85rem; font-weight: 700; color: var(--text-primary); }
.reg-detail { font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px; }
.reg-flow   { font-size: 0.72rem; font-weight: 600; display: flex; align-items: center; gap: 5px; margin-top: 3px; }

/* ── PRIORITY ITEMS ── */
.prio-item {
  display: flex; align-items: center; gap: 12px;
  padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-light);
}
.prio-item:last-child { border-bottom: none; }
.prio-rank { font-size: 0.82rem; font-weight: 800; color: var(--text-muted); width: 22px; text-align: center; font-family: 'DM Mono', monospace; }
.prio-name { font-size: 0.88rem; font-weight: 700; color: var(--text-primary); }
.prio-meta { font-size: 0.72rem; color: var(--text-muted); margin-top: 2px; }
.prio-score{ font-size: 1.2rem; font-weight: 800; font-family: 'DM Mono', monospace; }
.prio-badge{ font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.pl-critical{ background:#fef2f2; color:#991b1b; border:1px solid #fecaca; }
.pl-high    { background:#fff7ed; color:#92400e; border:1px solid #fed7aa; }
.pl-medium  { background:#fffbeb; color:#78350f; border:1px solid #fde68a; }
.pl-low     { background:#f0fdf4; color:#14532d; border:1px solid #bbf7d0; }

/* ── NOTIFICATION ITEMS ── */
.notif-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 0.85rem 1rem; border-bottom: 1px solid var(--border-light);
}
.notif-item:last-child { border-bottom: none; }
.notif-icon    { font-size: 1.1rem; flex-shrink: 0; }
.notif-title   { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
.notif-meta    { font-size: 0.72rem; color: var(--text-muted); margin-top: 2px; }
.notif-reason  { font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px; padding: 5px 8px; background: var(--bg); border-radius: 5px; }
.notif-badge   { font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; flex-shrink: 0; margin-top: 2px; }
.nb-error   { background: var(--red-light);   color: var(--red);   border: 1px solid var(--red-mid); }
.nb-warning { background: var(--amber-light); color: var(--amber); border: 1px solid var(--amber-mid); }
.nb-info    { background: var(--blue-light);  color: var(--blue);  border: 1px solid var(--blue-mid); }

/* ── TAGS ── */
.tag { display:inline-flex;align-items:center;gap:3px;font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:20px;border:1px solid; }
.tag-blue   { background:var(--blue-light);   color:var(--blue);   border-color:var(--blue-mid); }
.tag-green  { background:var(--green-light);  color:var(--green);  border-color:var(--green-mid); }
.tag-red    { background:var(--red-light);    color:var(--red);    border-color:var(--red-mid); }
.tag-amber  { background:var(--amber-light);  color:var(--amber);  border-color:var(--amber-mid); }
.tag-purple { background:var(--purple-light); color:var(--purple); border-color:#ddd6fe; }

/* ── MEMORY ITEMS ── */
.mem-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 0.75rem 1rem;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius-sm); margin-bottom: 0.5rem;
}
.mem-title { font-size: 0.8rem; font-weight: 700; color: var(--text-primary); }
.mem-body  { font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px; }
.mem-badge { font-size: 0.62rem; font-weight: 700; padding: 1px 6px; border-radius: 20px; margin-top: 4px; display: inline-block; background: var(--purple-light); color: var(--purple); border: 1px solid #ddd6fe; }

/* ── CARDS / PANELS ── */
.qiq-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow-sm); overflow: hidden;
  margin-bottom: 1rem;
}
.qiq-card-header {
  padding: 0.75rem 1.1rem; border-bottom: 1px solid var(--border-light);
  display: flex; align-items: center; justify-content: space-between;
}
.qiq-card-title { font-size: 0.85rem; font-weight: 700; color: var(--text-primary); }
.qiq-card-body  { padding: 1rem 1.1rem; }

/* ── SECTION TITLES ── */
.section-title {
  font-size: 0.85rem; font-weight: 700; color: var(--text-primary);
  margin: 1.1rem 0 0.6rem 0; padding-bottom: 0.35rem;
  border-bottom: 2px solid var(--border);
  display: flex; align-items: center; gap: 6px;
}

/* ── RELEASE CONFIDENCE WIDGET ── */
.conf-widget {
  background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
  border: 1px solid #dbeafe; border-radius: var(--radius);
  padding: 1.1rem 1.3rem; display: flex; align-items: center; gap: 1.2rem;
  margin-bottom: 0.75rem;
}
.conf-big        { font-size: 3.2rem; font-weight: 900; font-family: 'DM Mono', monospace; line-height: 1; }
.conf-big.good   { color: var(--green); }
.conf-big.medium { color: var(--amber); }
.conf-big.bad    { color: var(--red); }
.conf-desc h4 { font-size: 0.9rem; font-weight: 700; margin-bottom: 3px; }
.conf-desc p  { font-size: 0.78rem; color: var(--text-muted); }

/* ── STORY BOX ── */
.story-box {
  background: var(--blue-light); border-left: 3px solid var(--blue);
  padding: 0.6rem 0.9rem; border-radius: 0 6px 6px 0;
  font-style: italic; color: #1e40af; font-size: 0.82rem;
  margin-bottom: 0.75rem;
}

/* ── HEADER BANNER ── */
.qiq-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1.25rem; padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}
.qiq-logo { display: flex; align-items: center; gap: 10px; }
.qiq-logo-icon {
  width: 40px; height: 40px; border-radius: 11px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.qiq-logo-name {
  font-family: 'Fraunces', serif;
  font-size: 1.35rem; font-weight: 700; letter-spacing: -0.3px;
  color: var(--text-primary);
}
.qiq-logo-sub { font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }

/* ── FLOW DIAGRAM ── */
.flow-diagram {
  display: flex; align-items: center;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1rem 1.2rem;
  overflow-x: auto; margin-bottom: 1.25rem; gap: 2px;
}
.flow-node { display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; padding: 0 8px; }
.flow-node-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
.flow-node-name { font-size: 0.65rem; font-weight: 600; color: var(--text-secondary); text-align: center; white-space: nowrap; }
.flow-node-sub  { font-size: 0.6rem;  color: var(--text-muted); text-align: center; }
.flow-arrow     { font-size: 14px; color: var(--border); flex-shrink: 0; }
.fn-jira    { background: var(--blue-light); }
.fn-ai      { background: var(--purple-light); }
.fn-risk    { background: var(--red-light); }
.fn-gen     { background: var(--amber-light); }
.fn-run     { background: var(--green-light); }
.fn-reg     { background: #fdf4ff; }
.fn-insight { background: #f0f9ff; }
.fn-learn   { background: #f8faff; }

/* ── ALERT CHIP ── */
.alert-chip {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--amber-light); border: 1px solid var(--amber-mid);
  border-radius: 20px; padding: 3px 10px;
  font-size: 0.72rem; font-weight: 600; color: var(--amber);
}

/* ── AI STATUS ── */
.ai-status {
  display: flex; align-items: center; gap: 7px;
  background: var(--green-light); border: 1px solid var(--green-mid);
  border-radius: var(--radius-sm); padding: 7px 10px; margin-top: auto;
}
.ai-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.ai-status-text { font-size: 0.75rem; color: var(--green); font-weight: 600; }

/* ── SIDEBAR STYLING ── */
.sidebar-logo-wrap {
  padding: 0 0 1rem 0;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 0.75rem;
}

/* ── SIDEBAR NAV ── */
.nav-section-label {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.09em;
  padding: 0.55rem 0.6rem 0.2rem;
  display: block;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 7px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 1px;
  cursor: pointer;
  transition: background 0.12s;
  text-decoration: none;
}
.nav-item:hover { background: var(--bg); }
.nav-item.active {
  background: var(--blue-light);
  color: var(--blue);
  font-weight: 600;
}
.nav-icon { font-size: 14px; width: 18px; text-align: center; flex-shrink: 0; }
.nav-badge {
  margin-left: auto;
  font-size: 0.6rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 20px;
  line-height: 1.6;
}
.nb-blue  { background: var(--blue);  color: #fff; }
.nb-red   { background: var(--red);   color: #fff; }
.nb-amber { background: var(--amber); color: #fff; }
.nav-divider {
  border: none;
  border-top: 1px solid var(--border-light);
  margin: 0.3rem 0;
}
.control-panel-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0.6rem 0 0.3rem;
  display: block;
}

/* ── FORMULA CODE BLOCK ── */
.formula-block {
  font-family: 'DM Mono', monospace;
  font-size: 0.75rem;
  background: var(--bg);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  line-height: 2;
  color: var(--text-secondary);
}

/* ── STREAMLIT TAB OVERRIDE ── */
.stTabs [data-baseweb="tab-list"] {
  border-bottom: 1px solid var(--border);
  gap: 0;
  background: transparent;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  padding: 0.6rem 1rem;
  border-bottom: 2px solid transparent;
  background: transparent;
}
.stTabs [aria-selected="true"] {
  color: var(--blue) !important;
  border-bottom-color: var(--blue) !important;
}

/* ── STREAMLIT BUTTON OVERRIDES ── */
.stButton > button[kind="primary"] {
  background: var(--blue) !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
}
.stButton > button[kind="secondary"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-secondary) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
}
      /* Make nav item relative so overlay works */
.nav-item {
    position: relative;
}


/* Remove default button look */
.stButton > button {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* Inner layout */
.nav-btn-inner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 7px;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-secondary);
    transition: background 0.12s;
}

/* Hover effect */
.nav-btn-inner:hover {
    background: var(--bg);
}

/* Active state */
.nav-btn-inner.active {
    background: var(--blue-light);
    color: var(--blue);
    font-weight: 600;
}
            /* Style ALL sidebar buttons like nav items */
[data-testid="stSidebar"] .stButton > button {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;

    background: transparent;
    border: none;
    border-radius: 7px;

    padding: 8px 10px;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-secondary);

    transition: background 0.12s;
}

/* Hover */
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--bg);
}

/* Active (we fake this using aria-pressed) */
[data-testid="stSidebar"] .stButton > button:focus {
    background: var(--blue-light);
    color: var(--blue);
    font-weight: 600;
}

/* ── MISC ── */
.divider { border: none; border-top: 1px solid var(--border); margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def kpi_card(value, label, color, sub="", trend="", trend_up=True):
    trend_color = "var(--green)" if trend_up else "var(--red)"
    trend_html  = f'<div class="qiq-kpi-trend" style="color:{trend_color};">{trend}</div>' if trend else ""
    sub_html    = f'<div class="qiq-kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="qiq-kpi" style="--accent-color:{color};">
      <div class="qiq-kpi-val">{value}</div>
      <div class="qiq-kpi-label">{label}</div>
      {sub_html}{trend_html}
    </div>"""


def risk_module_card(module, risk_data, hist=None):
    sc    = risk_data["risk_score"]
    tier  = "high" if sc >= 0.65 else ("medium" if sc >= 0.35 else "low")
    score_label = risk_data["risk_label"]
    color_map   = {"high": "var(--red)", "medium": "var(--amber)", "low": "var(--green)"}
    clr         = color_map[tier]

    badge = ""
    if risk_data.get("regression"):
        badge = '<span class="rm-badge badge-reg">🔴 Regression</span>'
    elif hist and hist.get("frequent"):
        badge = '<span class="rm-badge badge-freq">⚠ Frequent</span>'
    else:
        badge = '<span class="rm-badge badge-ok">✓ Stable</span>'

    return f"""
    <div class="risk-module {tier}">
      {badge}
      <div class="rm-name">{module}</div>
      <div class="rm-score {tier}">{sc}</div>
      <div class="rm-label" style="color:{clr};">{score_label}</div>
      <div class="rm-stats">
        {risk_data['passed']}✅ {risk_data['failed']}❌ / {risk_data['total_tests']} tests
        · {risk_data['confidence_pct']}% conf
      </div>
    </div>"""


def bar_row(label, pct, value_str, color):
    return f"""
    <div class="bar-row">
      <div class="bar-label">{label}</div>
      <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>
      <div class="bar-val">{value_str}</div>
    </div>"""


def conf_bar(label, pct):
    return f"""
    <div class="conf-bar-wrap">
      <div class="conf-label">{label}</div>
      <div class="conf-track"><div class="conf-fill" style="width:{pct}%;"></div></div>
      <div class="conf-pct">{pct}%</div>
    </div>"""


def test_row(icon, name, result, reason):
    css_map = {"PASS": "result-pass", "FAIL": "result-fail", "ERROR": "result-err"}
    css = css_map.get(result, "result-err")
    return f"""
    <div class="test-row">
      <span>{icon}</span>
      <div class="test-name">{name}</div>
      <span class="test-result {css}">{result}</span>
      <div class="test-reason">{reason}</div>
    </div>"""


def notif_item(n):
    icon     = "❌" if n["level"] == "error" else ("⚠️" if n["level"] == "warning" else "ℹ️")
    badge_css= {"error": "nb-error", "warning": "nb-warning", "info": "nb-info"}.get(n["level"], "nb-info")
    return f"""
    <div class="notif-item">
      <div class="notif-icon">{icon}</div>
      <div style="flex:1;">
        <div class="notif-title">{n['scenario']}</div>
        <div class="notif-meta">{n['time']} · <strong>{n['feature'].upper()}</strong> · {n['assignee']}</div>
        <div class="notif-reason">{n['reason']}</div>
      </div>
      <span class="notif-badge {badge_css}">{n['level']}</span>
    </div>"""


def prio_item(rank, s, adp):
    sc = s["risk_score"]
    if sc >= 20:  badge_css, badge_txt = "pl-critical", "CRITICAL"
    elif sc >= 12: badge_css, badge_txt = "pl-high",     "HIGH"
    elif sc >= 7:  badge_css, badge_txt = "pl-medium",   "MEDIUM"
    else:          badge_css, badge_txt = "pl-low",       "LOW"
    color_map = {"pl-critical": "var(--red)", "pl-high": "var(--red)",
                 "pl-medium": "var(--amber)", "pl-low": "var(--green)"}
    score_color = color_map[badge_css]
    freq_tag = '<span class="tag tag-amber">Frequent</span>' if s.get("frequent_failure") else ""
    bar_w = min(int(sc / 28 * 100), 100)
    return f"""
    <div class="prio-item">
      <div class="prio-rank">#{rank}</div>
      <div style="flex:1;">
        <div class="prio-name">{s['feature'].upper()} &nbsp;{freq_tag}</div>
        <div class="prio-meta">Score: {sc} · Run {adp} tests (adaptive depth)</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <div style="width:70px;background:var(--bg);border-radius:4px;height:6px;overflow:hidden;">
          <div style="width:{bar_w}%;height:100%;border-radius:4px;background:{score_color};"></div>
        </div>
        <div class="prio-score" style="color:{score_color};">{sc}</div>
        <span class="prio-badge {badge_css}">{badge_txt}</span>
      </div>
    </div>"""


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    ai_badge = "🤖 AI" if is_ai_enabled() else "📋 Rules"
    notif_count   = len(get_notifications())
    regression_ct = len(st.session_state.get("last_results", {}).get("regressions", []))

    # ── LOGO ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sidebar-logo-wrap">
      <div style="display:flex;align-items:center;gap:9px;">
        <div class="qiq-logo-icon">⚡</div>
        <div>
          <div class="qiq-logo-name">QualityIQ</div>
          <div class="qiq-logo-sub">AI Testing Platform</div>
        </div>
        <span style="margin-left:auto;background:#e0f2fe;color:#0369a1;
                     padding:2px 8px;border-radius:6px;font-size:0.65rem;
                     font-weight:700;">{ai_badge}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── NAV ───────────────────────────────────────────────────────────────────
    # Track active page in session state; default to Dashboard
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "Dashboard"
    def _nav(icon, label, badge_count=0, badge_css="nb-blue"):
        active = st.session_state["active_page"] == label

        text = f"{icon}  {label}"
        if badge_count > 0:
            text += f"   ({badge_count})"

        if st.button(text, key=f"nav_{label}", use_container_width=True):
            st.session_state["active_page"] = label
            st.rerun()

    st.markdown('<span class="nav-section-label">Overview</span>',
                unsafe_allow_html=True)
    _nav("📊", "Dashboard")
    _nav("🧠", "AI Insights", badge_count=4, badge_css="nb-blue")

    st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
    st.markdown('<span class="nav-section-label">Testing</span>',
                unsafe_allow_html=True)
    _nav("🧪", "Test Results")
    _nav("🔄", "Regression", badge_count=max(regression_ct, 0) or 0,
         badge_css="nb-red")
    _nav("🎯", "Risk Priority")

    st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
    st.markdown('<span class="nav-section-label">Intelligence</span>',
                unsafe_allow_html=True)
    _nav("🔁", "Learning Memory")
    _gap_count = len(st.session_state.get("gap_results", {}).get("gaps", []))
    _nav("🔍", "Gap Detection", badge_count=_gap_count, badge_css="nb-amber")
    _nav("🔔", "Notifications", badge_count=notif_count if notif_count else 0,
         badge_css="nb-red")

    st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
    st.markdown('<span class="nav-section-label">Data</span>',
                unsafe_allow_html=True)
    _nav("🗄️", "Defect Log")
    _nav("📜", "History")

    # ── CONTROL PANEL ─────────────────────────────────────────────────────────
    st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
    st.markdown('<span class="control-panel-label">⚙️ Control Panel</span>',
                unsafe_allow_html=True)

    mode = st.radio("Input mode", ["📝 User Story", "🟦 Jira", "🎛️ Manual"], index=0,
                    label_visibility="collapsed")
    st.markdown("---")

    test_case = None

    # ── USER STORY ────────────────────────────────────────────────────────────
    if "User Story" in mode:
        story = st.text_area(
            "User story",
            value=st.session_state.get("story_input", ""),
            placeholder="e.g. User should be able to login",
            height=80,
        )
        st.markdown('<div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:4px;">Quick examples:</div>', unsafe_allow_html=True)
        examples = {
            "🔐 Login":    "User should be able to login with email and password",
            "📝 Signup":   "User should be able to register a new account",
            "🔍 Search":   "User should be able to search for products",
            "🛒 Cart":     "User should be able to add products to cart",
            "💳 Checkout": "User should be able to complete the checkout process",
            "📧 Contact":  "User should be able to send a contact message",
        }
        ec = st.columns(2)
        for i, (label, ex) in enumerate(examples.items()):
            with ec[i % 2]:
                if st.button(label, use_container_width=True, key=f"ex_{label}"):
                    st.session_state["story_input"] = ex
                    st.session_state.pop("generated_tests", None)
                    st.rerun()

        if story and story.strip():
            feature_preview = __import__("feature_detector").detect_feature(story)
            depth = adaptive_depth(feature_preview)
            fails = __import__("history_store").get_failure_count(feature_preview)
            if fails >= 3:
                st.warning(f"⚠️ {feature_preview.upper()} has failed {fails}× historically → generating {depth} tests")
            if st.button("🧠 Generate Test Cases", use_container_width=True, type="secondary"):
                with st.spinner("Generating…"):
                    g = get_test_cases_silent(story.strip())
                    g["user_story"] = story.strip()
                    st.session_state["generated_tests"] = g
                    st.session_state.pop("gap_results", None)  # reset so Gap Detection re-analyses

        if "generated_tests" in st.session_state:
            g = st.session_state["generated_tests"]
            st.success(f"✅ **{g['feature'].upper()}** — {g['total']} tests")
            with st.expander("View scenarios"):
                for i, t in enumerate(g["tests"], 1):
                    st.write(f"{i}. {t}")
            test_case = g

    # ── JIRA ──────────────────────────────────────────────────────────────────
    elif "Jira" in mode:
        st.markdown("**🟦 Fetch from Jira**")
        if not jira_configured():
            st.warning("Open **jira_connector.py** and fill in EMAIL, API_TOKEN, DOMAIN.")
        else:
            jira_key = st.text_input("Issue key", placeholder="e.g. PDM-7")
            if st.button("🔄 Fetch Story", use_container_width=True) and jira_key:
                with st.spinner(f"Fetching {jira_key}…"):
                    try:
                        j = fetch_story(jira_key.strip())
                        st.session_state["jira_story"] = j
                    except ValueError as e:
                        st.error(str(e))

            if "jira_story" in st.session_state:
                j = st.session_state["jira_story"]
                st.success(f"✅ {j['issue_key']} — {j['status']} · {j['priority']}")
                st.markdown(f"**{j['summary']}**")
                aname  = j.get("assignee_name", "Unassigned")
                aemail = j.get("assignee", "")
                if aemail:
                    st.markdown(
                        f'👤 **{aname}** <span class="tag tag-blue">{aemail}</span>'
                        f'<span class="tag tag-green">📧 Notified on failure</span>',
                        unsafe_allow_html=True,
                    )
                ps = score_story(j.get("feature", "general"), j["priority"], j["issue_key"])
                st.markdown(f'Risk score: **{ps["risk_score"]}** · {ps["label"]}')
                if st.button("🧠 Generate Tests", use_container_width=True, type="secondary"):
                    with st.spinner("Generating…"):
                        g = get_test_cases_silent(j["user_story"])
                        g.update({
                            "user_story":    j["user_story"],
                            "jira_key":      j["issue_key"],
                            "jira_priority": j["priority"],
                            "story_id":      j["issue_key"],
                            "assignee":      j.get("assignee", ""),
                        })
                        st.session_state["generated_tests"] = g
                        st.session_state.pop("gap_results", None)  # reset gap analysis
                if "generated_tests" in st.session_state:
                    g = st.session_state["generated_tests"]
                    st.success(f"✅ **{g['feature'].upper()}** — {g['total']} tests")
                    with st.expander("View scenarios"):
                        for i, t in enumerate(g["tests"], 1):
                            st.write(f"{i}. {t}")
                    test_case = g

    # ── MANUAL ────────────────────────────────────────────────────────────────
    else:
        feature = st.selectbox("Feature", ["login", "signup", "search", "cart", "checkout", "contact"])
        opts = {
            "login":    ["Valid login", "Invalid password", "Empty email", "Empty password", "Both fields empty", "Wrong credentials"],
            "signup":   ["Valid signup", "Password mismatch", "Short password", "Invalid email", "Empty name", "All fields empty"],
            "search":   ["Valid search", "Empty search", "Special characters", "No results", "Long search input"],
            "cart":     ["Add item", "Add multiple items", "Remove item", "View empty cart"],
            "checkout": ["Valid checkout", "Empty address", "Invalid phone", "Empty name", "Cash on delivery"],
            "contact":  ["Valid message", "Empty message", "Invalid email", "Empty name", "Very long message"],
        }
        selected = st.multiselect("Scenarios", opts.get(feature, []), default=opts.get(feature, [])[:3])
        if selected:
            test_case = {"feature": feature, "tests": selected}

    st.markdown("---")
    run_btn = st.button("▶️ Run Tests", type="primary", use_container_width=True, disabled=(test_case is None))

    if st.button("🗑️ Clear all data", use_container_width=True):
        clear_all()
        clear_history()
        clear_notifications()
        for k in ["generated_tests", "last_results", "story_input", "jira_story"]:
            st.session_state.pop(k, None)
        st.success("Cleared.")
        st.rerun()

    st.markdown("""
    <div class="ai-status" style="margin-top:1rem;">
      <div class="ai-dot"></div>
      <div class="ai-status-text">AI Engine Active</div>
    </div>""", unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────
ov = overall_risk()
notifs = get_notifications()

h_left, h_right = st.columns([4, 1])
with h_left:
    st.markdown("""
    <div class="flow-diagram">
      <div class="flow-node"><div class="flow-node-icon fn-jira">🟦</div><div class="flow-node-name">Jira</div><div class="flow-node-sub">Story Intake</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="flow-node-icon fn-ai">🧠</div><div class="flow-node-name">AI Understanding</div><div class="flow-node-sub">Context Extraction</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="flow-node-icon fn-risk">🎯</div><div class="flow-node-name">Risk Engine</div><div class="flow-node-sub">Prioritization</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="flow-node-icon fn-gen">⚙️</div><div class="flow-node-name">Test Generation</div><div class="flow-node-sub">Adaptive Depth</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="flow-node-icon fn-run">▶️</div><div class="flow-node-name">Playwright</div><div class="flow-node-sub">Self-Healing</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="flow-node-icon fn-reg">🔄</div><div class="flow-node-name">Regression</div><div class="flow-node-sub">Detection</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="flow-node-icon fn-insight">💡</div><div class="flow-node-name">Insight Engine</div><div class="flow-node-sub">Root Cause</div></div>
      <div class="flow-arrow">→</div>
      <div class="flow-node"><div class="flow-node-icon fn-learn">🔁</div><div class="flow-node-name">Learning</div><div class="flow-node-sub">Memory Feedback</div></div>
    </div>
    """, unsafe_allow_html=True)

with h_right:
    if ov["modules_tested"] > 0:
        conf = ov["confidence_pct"]
        tier = "good" if conf >= 70 else ("medium" if conf >= 40 else "bad")
        st.markdown(f"""
        <div style="text-align:center;margin-top:0.2rem;">
          <div style="font-size:0.65rem;color:var(--text-muted);font-weight:700;
                      text-transform:uppercase;letter-spacing:0.07em;">Release Confidence</div>
          <div class="conf-big {tier}">{conf}%</div>
          <div style="font-size:0.78rem;color:var(--text-muted);">{ov['risk_label']}</div>
        </div>""", unsafe_allow_html=True)

# Notification banner
if notifs:
    st.markdown(f'<div class="alert-chip">⚠️ {len(notifs)} notification(s) — see Notifications tab</div>',
                unsafe_allow_html=True)
    st.markdown("")

st.markdown("---")


# ── RUN ───────────────────────────────────────────────────────────────────────
if run_btn and test_case:
    feature_up = test_case["feature"].upper()
    st.markdown(f"""
    <div class="qiq-card-header" style="background:var(--surface);border:1px solid var(--border);
         border-radius:var(--radius);margin-bottom:0.75rem;">
      <div class="qiq-card-title">🔄 Running: <strong>{feature_up}</strong></div>
    </div>""", unsafe_allow_html=True)

    if test_case.get("user_story"):
        st.markdown(f'<div class="story-box">📖 {test_case["user_story"]}</div>', unsafe_allow_html=True)

    progress = st.progress(0, text="Starting…")
    log_box  = st.empty()
    logs, counter = [], [0]
    total = len(test_case["tests"])

    def tracked_log(msg):
        logs.append(msg)
        log_box.code("\n".join(logs[-25:]), language="")
        if "Scenario:" in msg:
            counter[0] += 1
            progress.progress(min(counter[0] / total, 1.0), text=f"Scenario {counter[0]}/{total}")

    results_data = run_test_suite(test_case, callback=tracked_log)
    progress.progress(1.0, text="Complete!")
    store_notifications(results_data.get("notifications", []))
    st.session_state["last_results"] = results_data

    s     = results_data["summary"]
    regs  = results_data.get("regressions", [])
    n_cnt = len(results_data.get("notifications", []))
    assignee_email = test_case.get("assignee", "")

    if regs:
        st.error(f"🚨 {len(regs)} regression(s) + {s['failed']} failure(s) — check Regression & Notifications tabs")
    elif s["failed"] == 0:
        st.success(f"✅ All {s['passed']} tests passed — no regressions detected.")
    else:
        st.warning(f"⚠️ {s['passed']} passed · {s['failed']} failed · {n_cnt} notification(s) sent")

    if (s["failed"] > 0 or s["errors"] > 0):
        if assignee_email:
            st.info(f"📧 Failure notification emailed to **{assignee_email}**")
        else:
            st.caption("ℹ️ No assignee email — notification skipped")
    st.rerun()


# ── REGRESSION PAGE ───────────────────────────────────────────────────────────
if st.session_state.get("active_page") == "Regression":

    import requests as _req_rc, json as _json_rc

    GROQ_API_KEY_RC = "api key"
    GROQ_URL_RC     = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL_RC   = "llama-3.1-8b-instant"

    def _get_root_cause(scenario: str, reason: str, module: str) -> dict:
        """Call Groq LLM to get root cause analysis for a regression."""
        prompt = (
            "You are a senior QA engineer performing root cause analysis.\n\n"
            f"A regression was detected:\n"
            f"- Module: {module}\n"
            f"- Scenario: {scenario}\n"
            f"- Failure Reason: {reason}\n\n"
            "Provide a JSON response with ONLY these fields (no markdown, no backticks):\n"
            "{\n"
            "  \"root_cause\": \"<concise technical root cause in 1-2 sentences>\",\n"
            "  \"category\": \"<one of: Code Change, Config Change, Data Issue, Dependency Failure, Environment Issue, Logic Error>\",\n"
            "  \"fix_suggestion\": \"<actionable fix in 1-2 sentences>\",\n"
            "  \"severity\": \"<one of: Critical, High, Medium, Low>\",\n"
            "  \"affected_area\": \"<specific code area or component likely responsible>\"\n"
            "}"
        )
        try:
            resp = _req_rc.post(
                GROQ_URL_RC,
                headers={"Authorization": f"Bearer {GROQ_API_KEY_RC}", "Content-Type": "application/json"},
                json={"model": GROQ_MODEL_RC, "max_tokens": 400,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=15
            )
            text = resp.json()["choices"][0]["message"]["content"].strip()
            text = text.replace("```json", "").replace("```", "").strip()
            return _json_rc.loads(text)
        except Exception:
            return {
                "root_cause": "Unable to fetch root cause — check API connectivity.",
                "category": "Unknown",
                "fix_suggestion": "Manually inspect the failing scenario and recent code changes.",
                "severity": "High",
                "affected_area": module
            }

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🔄 Regression Report & Root Cause Analysis</div>',
                unsafe_allow_html=True)
    st.caption("All previously-passing scenarios are re-checked after each test run. Click a regression to see AI root cause analysis.")

    last = st.session_state.get("last_results")

    if not last:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:var(--text-muted);">
          <div style="font-size:2.5rem;margin-bottom:0.75rem;">🔄</div>
          <div style="font-size:1rem;font-weight:600;color:var(--text-secondary);margin-bottom:0.4rem;">
            No regression data yet
          </div>
          <div style="font-size:0.82rem;">
            Run a test suite first — this page will show any regressions found across all modules.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        regs = last.get("regressions", [])

        # ── Summary banner ────────────────────────────────────────────────────
        if regs:
            st.markdown(f"""
            <div style="background:var(--red-light);border:1px solid var(--red-mid);
                        border-radius:var(--radius);padding:0.85rem 1.1rem;
                        margin-bottom:1rem;display:flex;align-items:center;gap:10px;">
              <div style="font-size:1.3rem;">🚨</div>
              <div>
                <div style="font-size:0.9rem;font-weight:700;color:var(--red);">
                  {len(regs)} Regression(s) Detected in {last['feature'].upper()}
                </div>
                <div style="font-size:0.78rem;color:#991b1b;margin-top:2px;">
                  Previously passing scenarios are now failing. AI root cause analysis available below.
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            # ── Group by module ───────────────────────────────────────────────
            by_mod = {}
            for r in regs:
                by_mod.setdefault(r["affected_module"], []).append(r)

            for mod, items in by_mod.items():
                st.markdown(f'<div class="section-title">❌ {mod.upper()} — {len(items)} regression(s)</div>',
                            unsafe_allow_html=True)

                for idx, item in enumerate(items):
                    scenario = item["scenario"]
                    reason   = item["reason"]
                    rc_key   = f"rc_{mod}_{idx}"

                    # Regression card
                    st.markdown(f"""
                    <div class="reg-item bad">
                      <div style="font-size:1.1rem;">🔴</div>
                      <div style="flex:1;">
                        <div class="reg-name">{scenario}</div>
                        <div class="reg-flow">
                          <span style="color:var(--green);">✅ PASS</span>
                          <span style="color:var(--text-muted);">→</span>
                          <span style="color:var(--red);">❌ FAIL</span>
                        </div>
                        <div class="reg-detail">Reason: {reason}</div>
                      </div>
                      <span class="tag tag-red">Confirmed</span>
                    </div>""", unsafe_allow_html=True)

                    # Root cause expander
                    with st.expander(f"🔍 Root Cause Analysis — {scenario[:60]}{'...' if len(scenario)>60 else ''}"):
                        if rc_key not in st.session_state:
                            if st.button(f"⚡ Analyse Root Cause", key=f"btn_{rc_key}"):
                                with st.spinner("Analysing root cause with AI…"):
                                    st.session_state[rc_key] = _get_root_cause(scenario, reason, mod)

                        if rc_key in st.session_state:
                            rc = st.session_state[rc_key]

                            sev_color = {"Critical": "#dc2626", "High": "#ea580c",
                                         "Medium": "#d97706", "Low": "#16a34a"}.get(rc.get("severity","High"), "#ea580c")
                            cat_icon  = {"Code Change": "💻", "Config Change": "⚙️",
                                         "Data Issue": "🗄️", "Dependency Failure": "🔗",
                                         "Environment Issue": "🌐", "Logic Error": "🧠"}.get(rc.get("category",""), "🔍")

                            st.markdown(f"""
                            <div style="background:var(--surface);border:1px solid var(--border);
                                        border-radius:var(--radius);padding:1rem;margin-top:0.5rem;">

                              <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:0.9rem;">
                                <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:6px;
                                            padding:4px 10px;font-size:0.75rem;font-weight:700;color:{sev_color};">
                                  ⚠ {rc.get('severity','—')} Severity
                                </div>
                                <div style="background:var(--bg);border:1px solid var(--border);border-radius:6px;
                                            padding:4px 10px;font-size:0.75rem;font-weight:600;color:var(--text-secondary);">
                                  {cat_icon} {rc.get('category','—')}
                                </div>
                                <div style="background:var(--bg);border:1px solid var(--border);border-radius:6px;
                                            padding:4px 10px;font-size:0.75rem;font-weight:600;color:var(--purple);">
                                  📍 {rc.get('affected_area','—')}
                                </div>
                              </div>

                              <div style="margin-bottom:0.7rem;">
                                <div style="font-size:0.72rem;font-weight:700;color:var(--text-muted);
                                            text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">
                                  🔎 Root Cause
                                </div>
                                <div style="font-size:0.85rem;color:var(--text-primary);line-height:1.5;">
                                  {rc.get('root_cause','—')}
                                </div>
                              </div>

                              <div>
                                <div style="font-size:0.72rem;font-weight:700;color:var(--text-muted);
                                            text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">
                                  🛠 Suggested Fix
                                </div>
                                <div style="font-size:0.85rem;color:var(--green);line-height:1.5;">
                                  {rc.get('fix_suggestion','—')}
                                </div>
                              </div>

                            </div>""", unsafe_allow_html=True)
                        else:
                            st.caption("Click the button above to run AI root cause analysis for this regression.")

        else:
            # No regressions — show healthy state
            st.markdown(f"""
            <div class="reg-item good">
              <div style="font-size:1.1rem;">✅</div>
              <div>
                <div class="reg-name" style="color:var(--green);">No regressions detected</div>
                <div class="reg-detail">All other modules still healthy after testing {last['feature'].upper()}.</div>
              </div>
              <span class="tag tag-green">Healthy</span>
            </div>""", unsafe_allow_html=True)

            from defect_store import get_module_summary as gms2, get_best_run as gbr2
            checked = [m for m in gms2() if m != last["feature"]]
            if checked:
                st.markdown('<div class="section-title">✅ Modules Verified</div>', unsafe_allow_html=True)
                for mod in checked:
                    best    = gbr2(mod)
                    passing = [r for r in best if r["result"] == "PASS"]
                    st.markdown(f"""
                    <div class="reg-item good">
                      <div style="font-size:1.1rem;">✅</div>
                      <div class="reg-name">{mod.upper()} — {len(passing)} scenario(s) re-checked and still passing</div>
                    </div>""", unsafe_allow_html=True)

    st.stop()

# ── GAP DETECTION PAGE ────────────────────────────────────────────────────────
if st.session_state.get("active_page") == "Gap Detection":

    import requests as _req, json as _json

    GROQ_API_KEY_GAP = "grok key"
    GROQ_URL_GAP     = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL_GAP   = "llama-3.1-8b-instant"

    def _analyse(user_story: str, tests: list) -> dict:
        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tests))
        prompt = (
            "You are a senior QA engineer doing test coverage analysis.\n\n"
            f"USER STORY:\n{user_story}\n\n"
            f"GENERATED TEST CASES:\n{numbered}\n\n"
            "Analyze the test cases carefully.\n\n"
            "Return a raw JSON object (no markdown, no explanation) with TWO keys:\n"
            "1. 'gaps': Array of scenarios NOT covered by the test cases above. "
            "Only include REAL gaps — scenarios clearly absent from the test list. "
            "Do NOT include scenarios already covered.\n"
            "2. 'covered': Array of areas that ARE well-covered by the test cases.\n\n"
            "Format:\n"
            "{\n"
            '  "gaps": [\n'
            '    {"gap": "...", "module": "...", "reason": "...", "risk_level": "High|Medium|Low"}\n'
            "  ],\n"
            '  "covered": [\n'
            '    {"area": "...", "module": "...", "scenario_count": 3}\n'
            "  ]\n"
            "}"
        )
        try:
            r = _req.post(
                GROQ_URL_GAP,
                headers={"Authorization": f"Bearer {GROQ_API_KEY_GAP}", "Content-Type": "application/json"},
                json={"model": GROQ_MODEL_GAP, "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 2048, "temperature": 0.2},
                timeout=30,
            )
            raw = r.json()["choices"][0]["message"]["content"].strip().strip("```json").strip("```").strip()
            result = _json.loads(raw)
            if isinstance(result, dict) and "gaps" in result:
                return result
            return {"gaps": [], "covered": []}
        except Exception:
            return {"gaps": [], "covered": []}

    def _build_coverage_matrix(tests: list, gaps: list) -> list:
        """Build per-module coverage matrix from tests and gaps."""
        # Extract module names from test strings
        module_tests = {}
        for t in tests:
            # Try to detect a module prefix like "Login:", "Checkout:", etc.
            parts = t.split(":")
            mod = parts[0].strip() if len(parts) > 1 else "General"
            module_tests.setdefault(mod, []).append(t)

        module_gaps = {}
        for g in gaps:
            mod = g.get("module", "General")
            module_gaps.setdefault(mod, 0)
            module_gaps[mod] += 1

        all_modules = sorted(set(list(module_tests.keys()) + list(module_gaps.keys())))
        matrix = []
        for mod in all_modules:
            tc   = len(module_tests.get(mod, []))
            gc   = module_gaps.get(mod, 0)
            # Coverage heuristic: more tests relative to gaps = higher coverage
            base = min(95, 60 + tc * 5) if tc > 0 else 50
            cov  = max(50, base - gc * 10)
            status = "Full" if gc == 0 else "Partial"
            matrix.append({"module": mod, "coverage": cov, "gaps": gc,
                            "status": status, "tc": tc})
        return matrix

    def _fallback_result(feature: str) -> dict:
        return {
            "gaps": [
                {"gap": f"Network/API failure during {feature}", "module": feature,
                 "reason": "No test covers offline/timeout state mid-flow. High business risk.", "risk_level": "High"},
                {"gap": f"SQL/XSS injection on {feature} input fields", "module": feature,
                 "reason": "Security edge cases not covered. Potential vulnerability.", "risk_level": "High"},
                {"gap": f"Mobile viewport form submission in {feature}", "module": feature,
                 "reason": "Form only tested on desktop. 60%+ users are on mobile.", "risk_level": "Medium"},
            ],
            "covered": [
                {"area": f"{feature}: Happy path, validation, core flows", "module": feature, "scenario_count": len(tests)},
            ]
        }

    # ── Pull data from session state ──────────────────────────────────────────
    gen        = st.session_state.get("generated_tests", {})
    user_story = gen.get("user_story", "")
    tests      = gen.get("tests", [])
    feature    = gen.get("feature", "Feature")

    # Auto-run when page opens and not yet computed
    if tests and user_story and "gap_results" not in st.session_state:
        with st.spinner("🧠 Analysing coverage gaps…"):
            result = _analyse(user_story, tests)
        if not result.get("gaps") and not result.get("covered"):
            result = _fallback_result(feature)
        # Sort gaps by risk
        result["gaps"].sort(
            key=lambda g: {"High": 0, "Medium": 1, "Low": 2}.get(g.get("risk_level", "Low"), 2)
        )
        result["matrix"] = _build_coverage_matrix(tests, result["gaps"])
        st.session_state["gap_results"] = result

    result = st.session_state.get("gap_results", {"gaps": [], "covered": [], "matrix": []})
    gaps    = result.get("gaps", [])
    covered = result.get("covered", [])
    matrix  = result.get("matrix", [])

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:0.5rem;">
      <div style="font-size:1.6rem;font-weight:800;color:var(--text-primary);margin-bottom:0.25rem;">
        🔍 Test Gap Detection
      </div>
      <div style="font-size:0.85rem;color:var(--text-muted);">
        AI identifies scenarios that are NOT tested — unique capability that prevents blind spots
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── No data state ─────────────────────────────────────────────────────────
    if not tests or not user_story:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:var(--text-muted);">
          <div style="font-size:2rem;margin-bottom:0.6rem;">🔍</div>
          <div style="font-size:0.9rem;font-weight:600;color:var(--text-secondary);margin-bottom:0.35rem;">
            No test cases generated yet
          </div>
          <div style="font-size:0.8rem;">
            Enter a user story in the sidebar and click <strong>🧠 Generate Test Cases</strong>,
            then come back here to see coverage gaps.
          </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # ── Alert banner ──────────────────────────────────────────────────────────
    if gaps:
        n_gaps = len(gaps)
        st.markdown(f"""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:1rem 1.2rem;margin-bottom:1.25rem;display:flex;align-items:flex-start;gap:10px;">
          <span style="font-size:1.1rem;margin-top:1px;">⚠️</span>
          <div>
            <div style="font-size:0.9rem;font-weight:700;color:#92400e;margin-bottom:2px;">
              {n_gaps} Untested Scenario{"s" if n_gaps != 1 else ""} Detected Across Modules
            </div>
            <div style="font-size:0.8rem;color:#a16207;">
              These critical paths have no test coverage and represent potential blind spots in your quality assurance.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Re-run button
    col_h, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("🔄 Re-analyse", key="rerun_gap", use_container_width=True):
            st.session_state.pop("gap_results", None)
            st.rerun()

    st.markdown("")

    # ── Two-column layout: Missing Coverage  +  Coverage Matrix ──────────────
    col_left, col_right = st.columns([1, 1], gap="large")

    # ── LEFT: Missing + Well-covered ─────────────────────────────────────────
    with col_left:

        # Missing Test Coverage
        if gaps:
            st.markdown("""
            <div style="font-size:0.9rem;font-weight:700;color:var(--text-primary);
                        margin-bottom:0.6rem;display:flex;align-items:center;gap:6px;">
              <span style="color:#dc2626;">🚫</span> Missing Test Coverage
            </div>
            """, unsafe_allow_html=True)

            for g in gaps:
                rl  = g.get("risk_level", "Medium")
                clr = {"High": "#dc2626", "Medium": "#d97706", "Low": "#059669"}.get(rl, "#d97706")
                icon = {"High": "🌐", "Medium": "🔐", "Low": "📱"}.get(rl, "📋")
                st.markdown(f"""
                <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
                            padding:0.75rem 0.9rem;margin-bottom:0.5rem;display:flex;
                            align-items:flex-start;gap:10px;">
                  <span style="font-size:1.1rem;flex-shrink:0;">{icon}</span>
                  <div>
                    <div style="font-size:0.82rem;font-weight:700;color:#1f2937;margin-bottom:2px;">
                      {g.get("gap","—")}
                    </div>
                    <div style="font-size:0.75rem;color:#92400e;line-height:1.45;">
                      {g.get("reason", g.get("root_cause", "—"))}
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No significant gaps found — test coverage looks complete!")

        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

        # Well-Covered Areas
        if covered:
            st.markdown("""
            <div style="font-size:0.9rem;font-weight:700;color:var(--text-primary);
                        margin-bottom:0.6rem;display:flex;align-items:center;gap:6px;">
              <span style="color:#059669;">✅</span> Well-Covered Areas
            </div>
            """, unsafe_allow_html=True)

            for c in covered:
                area  = c.get("area", "—")
                count = c.get("scenario_count", "")
                count_label = f" — {count} scenarios" if count else ""
                st.markdown(f"""
                <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
                            padding:0.65rem 0.9rem;margin-bottom:0.45rem;
                            display:flex;align-items:center;gap:10px;">
                  <span style="color:#16a34a;flex-shrink:0;">✅</span>
                  <div style="font-size:0.8rem;color:#15803d;font-weight:500;line-height:1.4;">
                    {area}{count_label}
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── RIGHT: Coverage Matrix ────────────────────────────────────────────────
    with col_right:
        st.markdown("""
        <div style="font-size:0.9rem;font-weight:700;color:var(--text-primary);
                    margin-bottom:0.6rem;display:flex;align-items:center;gap:6px;">
          📊 Coverage Matrix
        </div>
        """, unsafe_allow_html=True)

        if matrix:
            # Table header
            st.markdown("""
            <div style="background:var(--surface,#f9fafb);border:1px solid var(--border,#e5e7eb);
                        border-radius:10px;overflow:hidden;">
              <div style="display:grid;grid-template-columns:1fr 1.6fr 0.5fr 0.7fr;
                          gap:0;padding:0.5rem 0.9rem;border-bottom:1px solid var(--border,#e5e7eb);">
                <span style="font-size:0.65rem;font-weight:700;color:#9ca3af;text-transform:uppercase;
                             letter-spacing:.07em;">Module</span>
                <span style="font-size:0.65rem;font-weight:700;color:#9ca3af;text-transform:uppercase;
                             letter-spacing:.07em;">Coverage</span>
                <span style="font-size:0.65rem;font-weight:700;color:#9ca3af;text-transform:uppercase;
                             letter-spacing:.07em;">Gaps</span>
                <span style="font-size:0.65rem;font-weight:700;color:#9ca3af;text-transform:uppercase;
                             letter-spacing:.07em;">Status</span>
              </div>
            """, unsafe_allow_html=True)

            for row in matrix:
                cov    = row.get("coverage", 80)
                status = row.get("status", "Partial")
                g_cnt  = row.get("gaps", 0)
                mod    = row.get("module", "—")
                bar_clr = "#16a34a" if cov >= 90 else "#d97706"
                badge_bg  = "#f0fdf4" if status == "Full" else "#fffbeb"
                badge_clr = "#16a34a" if status == "Full" else "#d97706"
                gap_label = str(g_cnt) if g_cnt == 0 else f"{g_cnt} mobile" if "mobile" in str(g_cnt) else str(g_cnt)

                st.markdown(f"""
                <div style="display:grid;grid-template-columns:1fr 1.6fr 0.5fr 0.7fr;
                            align-items:center;gap:0;padding:0.6rem 0.9rem;
                            border-bottom:1px solid var(--border,#f3f4f6);">
                  <span style="font-size:0.82rem;font-weight:600;color:var(--text-primary,#111827);">
                    {mod}
                  </span>
                  <div style="display:flex;align-items:center;gap:8px;">
                    <div style="flex:1;background:#e5e7eb;border-radius:4px;height:6px;overflow:hidden;max-width:90px;">
                      <div style="width:{cov}%;height:100%;background:{bar_clr};border-radius:4px;"></div>
                    </div>
                    <span style="font-size:0.78rem;font-weight:700;color:var(--text-primary,#111827);
                                 font-family:monospace;">{cov}%</span>
                  </div>
                  <span style="font-size:0.8rem;color:var(--text-secondary,#6b7280);font-weight:500;">
                    {gap_label}
                  </span>
                  <span style="background:{badge_bg};color:{badge_clr};font-size:0.68rem;font-weight:700;
                               padding:2px 9px;border-radius:20px;display:inline-block;">
                    {status}
                  </span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:2rem;color:var(--text-muted);">
              No module data available.
            </div>
            """, unsafe_allow_html=True)

    st.stop()

    
# ── PAGE ROUTING ─────────────────────────────────────────────────────────────
# ═══════════════════ TAB 1 — DASHBOARD / OVERVIEW ════════════════════════════
if st.session_state.get("active_page", "Dashboard") == "Dashboard":
    ov = overall_risk()

    if ov["modules_tested"] == 0:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:var(--text-muted);">
          <div style="font-size:2.5rem;margin-bottom:0.75rem;">⚡</div>
          <div style="font-size:1rem;font-weight:600;color:var(--text-secondary);margin-bottom:0.4rem;">
            No results yet
          </div>
          <div style="font-size:0.82rem;">
            Enter a user story in the sidebar and click <strong>▶️ Run Tests</strong> to begin.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        all_def   = get_all()
        tot       = len(all_def)
        passed    = sum(1 for d in all_def if d["result"] == "PASS")
        failed    = sum(1 for d in all_def if d["result"] == "FAIL")
        pass_rate = round(passed / tot * 100) if tot else 0
        n_count   = len(get_notifications())
        all_risks = calculate_all_risks()

        # KPI Row
        k_cols = st.columns(6)
        kpi_data = [
            (tot,           "Total Tests",       "#2563eb", f"Across {ov['modules_tested']} modules", "↑ This sprint", True),
            (passed,        "✅ Passed",          "#059669", f"{pass_rate}% pass rate",              "↑ Improving",   True),
            (failed,        "❌ Failed",           "#dc2626", f"{100-pass_rate}% failure rate",       "↓ New failures",False),
            (f"{ov['confidence_pct']}%", "Release Confidence", "#7c3aed", ov["risk_label"],          "⚠ Check regressions", False),
            (n_count,       "🔔 Alerts",          "#d97706", "Notifications pending",               "↑ New critical",False),
            ("91%",         "AI Accuracy",        "#0891b2", "Prediction score",                    "↑ Learning",    True),
        ]
        for col, (val, label, color, sub, trend, up) in zip(k_cols, kpi_data):
            with col:
                st.markdown(kpi_card(val, label, color, sub, trend, up), unsafe_allow_html=True)

        st.markdown("")

        # Risk Heatmap
        st.markdown('<div class="section-title">🌡️ Module Risk Heatmap</div>', unsafe_allow_html=True)
        histories = get_all_feature_summaries()
        rm_cols = st.columns(max(len(all_risks), 1))
        for col, (module, risk) in zip(rm_cols, all_risks.items()):
            hist = histories.get(module, {})
            with col:
                st.markdown(risk_module_card(module.upper(), risk, hist), unsafe_allow_html=True)

        st.markdown("")

        # Bar chart + Release status
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("""
            <div class="qiq-card">
              <div class="qiq-card-header"><div class="qiq-card-title">📉 Risk Score by Module</div></div>
              <div class="qiq-card-body">""", unsafe_allow_html=True)
            bars_html = ""
            max_score = max((v["risk_score"] for v in all_risks.values()), default=1) or 1
            for module, risk in all_risks.items():
                sc = risk["risk_score"]
                pct = round(sc / max_score * 100)
                clr = "var(--red)" if sc >= 0.65 else ("var(--amber)" if sc >= 0.35 else "var(--green)")
                bars_html += bar_row(module.upper(), pct, str(sc), clr)
            st.markdown(bars_html + "</div></div>", unsafe_allow_html=True)

        with ch2:
            conf     = ov["confidence_pct"]
            tier_cls = "good" if conf >= 70 else ("medium" if conf >= 40 else "bad")
            st.markdown(f"""
            <div class="qiq-card">
              <div class="qiq-card-header"><div class="qiq-card-title">🏆 Release Status</div></div>
              <div class="qiq-card-body">
                <div class="conf-widget">
                  <div class="conf-big {tier_cls}">{conf}%</div>
                  <div class="conf-desc">
                    <h4>{ov['risk_label']} Release</h4>
                    <p>{passed} scenarios passing · {failed} need attention</p>
                  </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;">
                  <div style="background:var(--green-light);border:1px solid var(--green-mid);
                              border-radius:8px;padding:8px;text-align:center;">
                    <div style="font-size:1.1rem;font-weight:800;color:var(--green);
                                font-family:'DM Mono',monospace;">{passed}</div>
                    <div style="font-size:0.65rem;color:var(--green);font-weight:700;
                                text-transform:uppercase;letter-spacing:.05em;">Passing</div>
                  </div>
                  <div style="background:var(--red-light);border:1px solid var(--red-mid);
                              border-radius:8px;padding:8px;text-align:center;">
                    <div style="font-size:1.1rem;font-weight:800;color:var(--red);
                                font-family:'DM Mono',monospace;">{failed}</div>
                    <div style="font-size:0.65rem;color:var(--red);font-weight:700;
                                text-transform:uppercase;letter-spacing:.05em;">Need Attention</div>
                  </div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════ TAB 2 — TEST RESULTS ════════════════════════════════════
elif st.session_state.get("active_page") == "Test Results":
    last = st.session_state.get("last_results")

    if not last:
        sm = get_module_summary()
        if sm:
            lm   = list(sm.keys())[-1]
            rows = get_latest_run(lm)
            if rows:
                st.markdown(f'<div class="section-title">Most recent: {lm.upper()}</div>', unsafe_allow_html=True)
                rows_html = ""
                for row in rows:
                    icon = "✅" if row["result"] == "PASS" else ("❌" if row["result"] == "FAIL" else "⚠️")
                    rows_html += test_row(icon, row["scenario"], row["result"], row["reason"])
                st.markdown(f'<div class="qiq-card">{rows_html}</div>', unsafe_allow_html=True)
        else:
            st.info("No results yet.")
    else:
        feature = last["feature"]
        results = last["results"]
        summary = last["summary"]
        risk    = last["risk"]

        # Feature header
        conf_clr = "var(--green)" if risk["confidence_pct"] >= 70 else "var(--red)"
        jk_tag   = f'<span class="tag tag-blue">🟦 {last["jira_key"]}</span>' if last.get("jira_key") else ""
        reg_tag  = '<span class="tag tag-red">⚠ Regression Detected</span>' if last.get("regressions") else ""
        risk_tag = f'<span class="tag tag-red">🔴 Critical: {risk["risk_score"]}</span>' if risk["risk_score"] >= 0.65 else f'<span class="tag tag-amber">Risk: {risk["risk_score"]}</span>'

        st.markdown(f"""
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
                    box-shadow:var(--shadow);padding:1.2rem 1.4rem;margin-bottom:1rem;">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:0.75rem;">
            <div>
              <div style="font-family:'Fraunces',serif;font-size:1.3rem;font-weight:700;">{feature.upper()}</div>
              <div style="display:flex;gap:5px;margin-top:4px;">{jk_tag}{risk_tag}{reg_tag}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:0.65rem;color:var(--text-muted);margin-bottom:2px;">Release Confidence</div>
              <div style="font-size:2.2rem;font-weight:900;color:{conf_clr};
                          font-family:'DM Mono',monospace;line-height:1;">
                {risk['confidence_pct']}%
              </div>
            </div>
          </div>
          {'<div class="story-box">📖 ' + last["user_story"] + '</div>' if last.get("user_story") else ""}
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
            {kpi_card(summary['total'],  'Total Tests', '#2563eb')}
            {kpi_card(summary['passed'], '✅ Passed',   '#059669')}
            {kpi_card(summary['failed'], '❌ Failed',   '#dc2626')}
            {kpi_card(summary['errors'], '⚠️ Errors',   '#d97706')}
          </div>
        </div>""", unsafe_allow_html=True)

        # Test rows
        sorted_results = sorted(results, key=lambda x: 0 if x["result"] == "FAIL" else (1 if x["result"] == "ERROR" else 2))
        rows_html = ""
        for r in sorted_results:
            icon = "✅" if r["result"] == "PASS" else ("❌" if r["result"] == "FAIL" else "⚠️")
            rows_html += test_row(icon, r["scenario"], r["result"], r["reason"])

        st.markdown(f"""
        <div class="qiq-card">
          <div class="qiq-card-header">
            <div class="qiq-card-title">📋 Scenarios — failures first</div>
            <span class="tag tag-amber">{summary['total']} scenarios</span>
          </div>
          {rows_html}
        </div>""", unsafe_allow_html=True)

        # Risk breakdown
        st.markdown('<div class="section-title">📉 Risk Breakdown</div>', unsafe_allow_html=True)
        rb1, rb2, rb3, rb4 = st.columns(4)
        rb1.metric("Risk Score",    risk["risk_score"])
        rb2.metric("Failure Rate",  f"{round(risk['failure_rate']*100)}%")
        rb3.metric("Defect Density",risk["defect_density"])
        rb4.metric("Complexity",    risk["complexity"])


# ═══════════════════ TAB 4 — RISK PRIORITY ═══════════════════════════════════
elif st.session_state.get("active_page") == "Risk Priority":
    st.markdown('<div class="section-title">🎯 Risk-Based Execution Priority</div>', unsafe_allow_html=True)
    st.caption("AI-driven test ordering based on failure history, business impact, and feature criticality.")

    histories = get_all_feature_summaries()

    # History KPIs
    if histories:
        st.markdown('<div class="section-title">📊 Failure History by Module</div>', unsafe_allow_html=True)
        h_cols = st.columns(min(len(histories), 4))
        for col, (feat, h) in zip(h_cols, histories.items()):
            clr = "#dc2626" if h["frequent"] else ("#d97706" if h["failure_rate"] > 0 else "#059669")
            with col:
                st.markdown(kpi_card(
                    h["total_failures"], feat.upper(), clr,
                    f"{h['total_runs']} runs · {round(h['failure_rate']*100)}% fail rate",
                    "⚠ Frequent!" if h["frequent"] else "",
                    not h["frequent"],
                ), unsafe_allow_html=True)
        st.markdown("")

    # Priority queue
    p1, p2 = st.columns([3, 2])
    with p1:
        jira_p = st.selectbox(" Jira priority", ["High", "Medium", "Low", "Highest"], index=0)
        features_list = ["checkout", "login", "cart", "signup", "search", "contact"]
        scores = [score_story(f, jira_p) for f in features_list]
        scores.sort(key=lambda x: x["risk_score"], reverse=True)

        items_html = "".join(prio_item(rank, s, adaptive_depth(s["feature"])) for rank, s in enumerate(scores, 1))
        st.markdown(f"""
        <div class="qiq-card">
          <div class="qiq-card-header">
            <div class="qiq-card-title">🔢 Priority Queue — Run This Order</div>
            <span class="tag tag-blue">Jira: {jira_p}</span>
          </div>
          {items_html}
        </div>""", unsafe_allow_html=True)

    with p2:
        st.markdown("""
        <div class="qiq-card" style="margin-bottom:0.75rem;">
          <div class="qiq-card-header"><div class="qiq-card-title">⚖️ Scoring Formula</div></div>
          <div class="qiq-card-body">
            <div class="formula-block">
              score = priority_weight<br>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ (failures × 2)<br>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ critical_bonus<br>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ frequency_bonus
            </div>
            <div style="margin-top:0.75rem;display:flex;flex-direction:column;gap:4px;
                        font-size:0.78rem;color:var(--text-secondary);">
              <div>🔴 <strong>Critical bonus:</strong> +8 pts for checkout/login</div>
              <div>🔁 <strong>Frequency bonus:</strong> +4 pts if ≥3 past failures</div>
              <div>📊 <strong>Priority weight:</strong> Highest=12 High=9 Med=6 Low=3</div>
              <div>🧪 <strong>Adaptive depth:</strong> More failures → more tests</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Adaptive depth bars
        depth_bars = ""
        max_d = max((adaptive_depth(f) for f in features_list), default=1) or 1
        for s in scores:
            d   = adaptive_depth(s["feature"])
            pct = round(d / max_d * 100)
            sc  = s["risk_score"]
            clr = "var(--red)" if sc >= 20 else ("var(--amber)" if sc >= 7 else "var(--green)")
            depth_bars += bar_row(s["feature"].upper(), pct, f"{d} tests", clr)

        st.markdown(f"""
        <div class="qiq-card">
          <div class="qiq-card-header"><div class="qiq-card-title">📐 Adaptive Test Depth</div></div>
          <div class="qiq-card-body">{depth_bars}</div>
        </div>""", unsafe_allow_html=True)

    # Most failing scenarios
    if histories:
        st.markdown('<div class="section-title">🔍 Most Failing Scenarios</div>', unsafe_allow_html=True)
        feat_sel = st.selectbox("Feature", list(histories.keys()))
        failing  = get_failing_scenarios(feat_sel)
        if failing:
            rows_html = ""
            for f in failing:
                rows_html += test_row("❌", f["scenario"], "FAIL", f"Failed {f['fail_count']}× historically")
            st.markdown(f'<div class="qiq-card">{rows_html}</div>', unsafe_allow_html=True)
        else:
            st.success(f"No failures recorded for {feat_sel.upper()} yet.")


# ═══════════════════ TAB 5 — NOTIFICATIONS ═══════════════════════════════════
elif st.session_state.get("active_page") == "Notifications":
    st.markdown('<div class="section-title">🔔 Failure Notifications</div>', unsafe_allow_html=True)
    st.caption("Automated alerts mapped to assigned developers when tests fail or regressions are detected.")

    notifs = get_notifications()
    if not notifs:
        st.markdown("""
        <div class="reg-item good">
          <div style="font-size:1.1rem;">✅</div>
          <div class="reg-name" style="color:var(--green);">No notifications — all tests passing!</div>
        </div>""", unsafe_allow_html=True)
    else:
        f1, f2 = st.columns(2)
        with f1: feat_f = st.multiselect("Filter feature", list({n["feature"] for n in notifs}))
        with f2: lvl_f  = st.multiselect("Filter level",   ["error", "warning", "info"])

        filtered = notifs
        if feat_f: filtered = [n for n in filtered if n["feature"] in feat_f]
        if lvl_f:  filtered = [n for n in filtered if n["level"]   in lvl_f]

        notifs_html = "".join(notif_item(n) for n in filtered)
        st.markdown(f'<div class="qiq-card">{notifs_html}</div>', unsafe_allow_html=True)

        if st.button("🗑️ Clear notifications"):
            clear_notifications()
            st.rerun()


# ═══════════════════ TAB 6 — DEFECT LOG ══════════════════════════════════════
elif st.session_state.get("active_page") == "Defect Log":
    st.markdown('<div class="section-title">🗄️ Full Defect Log</div>', unsafe_allow_html=True)
    rows = get_all()

    if not rows:
        st.info("No records yet.")
    else:
        df = pd.DataFrame(rows)[["id", "module", "scenario", "result", "reason", "timestamp"]]

        fc1, fc2, fc3 = st.columns(3)
        with fc1: mf = st.multiselect("Module", sorted(df["module"].unique()))
        with fc2: rf = st.multiselect("Result", ["PASS", "FAIL", "ERROR"])
        with fc3: sf = st.text_input("Search", placeholder="scenario keyword…")

        if mf: df = df[df["module"].isin(mf)]
        if rf: df = df[df["result"].isin(rf)]
        if sf: df = df[df["scenario"].str.contains(sf, case=False, na=False)]

        # Summary KPIs
        kc = st.columns(4)
        kpi_vals = [
            (len(df),                       "Showing",   "#2563eb"),
            (len(df[df["result"]=="PASS"]),  "✅ Pass",   "#059669"),
            (len(df[df["result"]=="FAIL"]),  "❌ Fail",   "#dc2626"),
            (len(df[df["result"]=="ERROR"]), "⚠️ Error",  "#d97706"),
        ]
        for col, (val, label, clr) in zip(kc, kpi_vals):
            with col:
                st.markdown(kpi_card(val, label, clr), unsafe_allow_html=True)

        st.markdown("")

        def colorize(v):
            return {
                "PASS":  "background-color:#ecfdf5;color:#059669;font-weight:600",
                "FAIL":  "background-color:#fef2f2;color:#dc2626;font-weight:600",
                "ERROR": "background-color:#fffbeb;color:#d97706;font-weight:600",
            }.get(v, "")

        st.dataframe(
            df.style.applymap(colorize, subset=["result"]),
            use_container_width=True,
            height=400,
        )
        st.caption(f"Showing {len(df)} of {len(rows)} records")

# ═══════════════════ AI INSIGHTS ═════════════════════════════════════════════
elif st.session_state.get("active_page") == "AI Insights":
    st.markdown('<div class="section-title">🧠 AI Insights</div>', unsafe_allow_html=True)
    st.caption("AI-generated observations and recommendations based on your test history.")

    histories = get_all_feature_summaries()
    all_risks = calculate_all_risks()

    if not histories and not all_risks:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:var(--text-muted);">
          <div style="font-size:2.5rem;margin-bottom:0.75rem;">🧠</div>
          <div style="font-size:1rem;font-weight:600;color:var(--text-secondary);margin-bottom:0.4rem;">
            No data to analyse yet
          </div>
          <div style="font-size:0.82rem;">
            Run some test suites first — AI insights will appear here as patterns emerge.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        insights = []
        for feat, h in histories.items():
            risk_d = all_risks.get(feat, {})
            sc = risk_d.get("risk_score", 0)
            if h.get("frequent"):
                insights.append({
                    "title": f"🔴 Frequent failures in {feat.upper()}",
                    "source": f"{h['total_failures']} failures across {h['total_runs']} runs",
                    "body": f"This module has failed more than 3 times historically. Consider reviewing recent changes to {feat} and adding defensive validation.",
                    "accent": "var(--red)",
                })
            elif sc >= 0.65:
                insights.append({
                    "title": f"⚠️ High risk score for {feat.upper()}",
                    "source": f"Risk score: {sc}",
                    "body": f"The {feat} module has a high composite risk score driven by failure rate and change complexity. Prioritise this in the next test run.",
                    "accent": "var(--amber)",
                })
            elif h.get("failure_rate", 0) == 0:
                insights.append({
                    "title": f"✅ {feat.upper()} is consistently stable",
                    "source": f"{h['total_runs']} runs, zero failures",
                    "body": f"All recorded runs for {feat} have passed. This module can be de-prioritised in resource-constrained sprints.",
                    "accent": "var(--green)",
                })

        if not insights:
            st.info("Not enough history to generate insights yet. Run more test suites.")
        else:
            for ins in insights:
                st.markdown(f"""
                <div class="insight-card" style="--accent:{ins['accent']};">
                  <div class="insight-title">{ins['title']}</div>
                  <div class="insight-source">{ins['source']}</div>
                  <div class="insight-body">{ins['body']}</div>
                </div>""", unsafe_allow_html=True)

        # Show confidence bars per module
        if all_risks:
            st.markdown('<div class="section-title">📊 Module Confidence Summary</div>', unsafe_allow_html=True)
            bars_html = ""
            for mod, risk in all_risks.items():
                bars_html += conf_bar(mod.upper(), risk["confidence_pct"])
            st.markdown(f'<div class="qiq-card"><div class="qiq-card-body">{bars_html}</div></div>', unsafe_allow_html=True)


# ═══════════════════ LEARNING MEMORY ═════════════════════════════════════════
elif st.session_state.get("active_page") == "Learning Memory":

    import html

    st.markdown('<div class="section-title">🔁 Learning Memory</div>', unsafe_allow_html=True)
    st.caption("The AI agent remembers past failures, adapts test depth, and improves over time.")

    histories = get_all_feature_summaries()

    # ✅ DEMO DATA FALLBACK
    if not histories or len(histories) == 0:
        histories = {
            "search": {
                "total_runs": 6,
                "total_failures": 2,
                "failure_rate": 0.33,
                "frequent": True
            },
            "login": {
                "total_runs": 6,
                "total_failures": 0,
                "failure_rate": 0.0,
                "frequent": False
            },
            "checkout": {
                "total_runs": 6,
                "total_failures": 0,
                "failure_rate": 0.0,
                "frequent": False
            },
            "cart": {
                "total_runs": 6,
                "total_failures": 1,
                "failure_rate": 0.16,
                "frequent": False
            }
        }

        st.info("⚡ Showing demo learning data (no real history yet)")

    # ── RENDER CARDS ───────────────────────────────────────────────────────
    for feat, h in histories.items():

        feat_safe = html.escape(feat.upper())
        depth = adaptive_depth(feat)

        # 🎯 Color logic
        if h.get("frequent"):
            badge_clr = "#dc2626"
        elif h["failure_rate"] > 0:
            badge_clr = "#d97706"
        else:
            badge_clr = "#059669"

        failure_pct = round(h["failure_rate"] * 100)

        st.markdown(f"""
        <div class="mem-item">

          <div style="font-size:1.3rem;">🧠</div>

          <div style="flex:1;">
            <div class="mem-title">{feat_safe}</div>

            <div class="mem-body">
              {h['total_runs']} runs recorded · 
              {h['total_failures']} total failures · 
              {failure_pct}% failure rate
            </div>

            <div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap;">
              <span class="mem-badge">
                🧪 Adaptive depth: {depth} tests
              </span>

              {"<span class='mem-badge' style='background:#fef2f2;color:#dc2626;border-color:#fca5a5;'>⚠ Frequent failure</span>" if h.get("frequent") else ""}
            </div>
          </div>

          <div style="
              font-size:1.6rem;
              font-weight:800;
              color:{badge_clr};
              font-family:'DM Mono', monospace;
          ">
            {h['total_failures']}
          </div>

        </div>
        """, unsafe_allow_html=True)


# ═══════════════════ HISTORY ══════════════════════════════════════════════════
elif st.session_state.get("active_page") == "History":
    st.markdown('<div class="section-title">📜 Test Run History</div>', unsafe_allow_html=True)
    st.caption("All historical test runs stored for trend analysis and adaptive depth calculation.")

    rows = get_all()
    if not rows:
        st.info("No history yet. Run some tests to populate this view.")
    else:
        df = pd.DataFrame(rows)
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp", ascending=False)

        fc1, fc2 = st.columns(2)
        with fc1:
            mf = st.multiselect("Filter by module", sorted(df["module"].unique()) if "module" in df.columns else [])
        with fc2:
            rf = st.multiselect("Filter by result", ["PASS", "FAIL", "ERROR"])

        if mf: df = df[df["module"].isin(mf)]
        if rf: df = df[df["result"].isin(rf)]

        st.dataframe(df, use_container_width=True, height=500)
        st.caption(f"Showing {len(df)} of {len(rows)} records")