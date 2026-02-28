"""
main.py — JobSeekAI · Bangladesh Job Market Intelligence
UI: Stone & Gold — Editorial Intelligence aesthetic
"""

from __future__ import annotations
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import streamlit as st

st.set_page_config(
    page_title="JobSeekAI — BD Market Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ai_summary import (
    generate_market_summary, generate_job_recommendations,
    analyze_skill_gap, estimate_salary,
)
from utils import (
    apply_filters, get_filter_options, load_data,
    most_common_value, top_skills_list,
    get_delta_jobs, get_jobs_today, get_new_companies_today, get_data_freshness,
    to_csv_bytes, to_pdf_bytes,
    get_degree_counts, get_experience_level_counts, get_industry_education_matrix,
    get_company_intel, get_top_companies_list,
)
from visualizations import (
    plot_industry_distribution, plot_top_companies, plot_location_distribution,
    plot_posting_trend,
    plot_degree_demand, plot_experience_levels, plot_industry_education_heatmap,
)

# ══════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — STONE & GOLD  ·  Editorial Intelligence
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600;700&family=DM+Mono:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">

<style>
/* ─────────────────────────────────────────────────────────────────────
   TOKEN SYSTEM
───────────────────────────────────────────────────────────────────── */
:root {
  /* Stone palette — warm off-whites to deep ink */
  --stone-25 : #fdfcfa;
  --stone-50 : #fafaf8;
  --stone-100: #f5f4f0;
  --stone-150: #eeece6;
  --stone-200: #e5e2da;
  --stone-300: #ccc8be;
  --stone-400: #a8a398;
  --stone-500: #857f74;
  --stone-600: #645f56;
  --stone-700: #46423b;
  --stone-800: #2e2b25;
  --stone-900: #1a1814;
  --stone-950: #0d0c0a;

  /* Gold palette — warm saffron accent */
  --gold-100: #fef7e0;
  --gold-200: #fdedb8;
  --gold-300: #f9d978;
  --gold-400: #f0c040;
  --gold-500: #c9a84c;
  --gold-600: #a8872e;
  --gold-700: #856a1e;
  --gold-800: #5c4a15;

  /* Slate-cool — secondary accent family */
  --slate-50 : #f0f4f8;
  --slate-100: #dae4ef;
  --slate-200: #b8cedf;
  --slate-300: #89aec8;
  --slate-400: #5a8eae;
  --slate-500: #3d7094;
  --slate-600: #2f5874;
  --slate-700: #234358;
  --slate-800: #182f3e;

  /* Rose-dust — tertiary / negative */
  --rose-50 : #fdf2f2;
  --rose-100: #fce4e4;
  --rose-200: #f8c4c4;
  --rose-400: #e87575;
  --rose-500: #d85555;
  --rose-600: #b83838;
  --rose-700: #8f2424;

  /* Sage — positive / growth */
  --sage-50 : #f2f7f3;
  --sage-100: #dceee0;
  --sage-200: #b5d9bc;
  --sage-400: #6aae78;
  --sage-500: #4a9459;
  --sage-600: #347544;
  --sage-700: #235730;

  /* Semantic */
  --bg          : var(--stone-50);
  --bg-surface  : #ffffff;
  --bg-subtle   : var(--stone-100);
  --bg-muted    : var(--stone-150);

  --border-faint : rgba(168,163,152,0.18);
  --border-base  : rgba(168,163,152,0.35);
  --border-strong: rgba(168,163,152,0.6);
  --border-gold  : rgba(201,168,76,0.4);

  --text-ink     : var(--stone-900);
  --text-body    : var(--stone-700);
  --text-muted   : var(--stone-500);
  --text-faint   : var(--stone-400);

  --accent       : var(--gold-500);
  --accent-light : var(--gold-100);
  --accent-dark  : var(--gold-700);

  /* Typography */
  --font-display : 'Cormorant Garamond', Georgia, serif;
  --font-sans    : 'Outfit', system-ui, sans-serif;
  --font-mono    : 'DM Mono', 'Fira Code', monospace;

  /* Elevation shadows (warm-tinted) */
  --shadow-xs : 0 1px 2px rgba(26,24,20,0.05);
  --shadow-sm : 0 1px 4px rgba(26,24,20,0.07), 0 1px 2px rgba(26,24,20,0.04);
  --shadow-md : 0 4px 12px rgba(26,24,20,0.08), 0 2px 4px rgba(26,24,20,0.04);
  --shadow-lg : 0 12px 28px rgba(26,24,20,0.09), 0 4px 8px rgba(26,24,20,0.05);
  --shadow-xl : 0 24px 48px rgba(26,24,20,0.10), 0 8px 16px rgba(26,24,20,0.05);
  --shadow-gold: 0 4px 16px rgba(201,168,76,0.22), 0 1px 4px rgba(201,168,76,0.12);

  /* Spacing (8pt grid) */
  --s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:20px;
  --s6:24px;--s7:28px;--s8:32px;--s10:40px;--s12:48px;--s16:64px;

  /* Radius */
  --r-xs:4px;--r-sm:6px;--r-md:10px;--r-lg:14px;--r-xl:20px;--r-2xl:28px;
}

/* ─────────────────────────────────────────────────────────────────────
   GLOBAL BASE
───────────────────────────────────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"], .main {
  background : var(--bg) !important;
  font-family: var(--font-sans) !important;
  color      : var(--text-ink) !important;
}

/* Warm paper-grain texture overlay */
[data-testid="stAppViewContainer"]::before {
  content  : '';
  position : fixed;
  inset    : 0;
  background:
    radial-gradient(ellipse 1200px 800px at 15% 0%,
      rgba(201,168,76,0.04) 0%, transparent 65%),
    radial-gradient(ellipse 900px 700px at 90% 100%,
      rgba(61,112,148,0.03) 0%, transparent 65%),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.015'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index  : 0;
}

/* Hide Streamlit chrome */
#MainMenu,footer,[data-testid="stToolbar"],
[data-testid="stDecoration"]{ display:none !important; }

.block-container {
  padding-top  : 0 !important;
  padding-left : 2.5rem !important;
  padding-right: 2.5rem !important;
  max-width    : 1360px !important;
  position     : relative;
  z-index      : 1;
}

hr {
  border    : none !important;
  border-top: 1px solid var(--border-base) !important;
  margin    : var(--s12) 0 !important;
}

/* ─────────────────────────────────────────────────────────────────────
   SIDEBAR
───────────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background  : var(--bg-surface) !important;
  border-right: 1px solid var(--border-base) !important;
  box-shadow  : 2px 0 12px rgba(26,24,20,0.04) !important;
}
[data-testid="stSidebar"] > div {
  padding: var(--s8) var(--s6) !important;
}
[data-testid="stSidebar"] * {
  font-family: var(--font-sans) !important;
  color      : var(--text-ink) !important;
}
/* Multiselect tags */
[data-testid="stSidebar"] span[data-baseweb="tag"] {
  background  : var(--gold-100) !important;
  border      : 1px solid var(--border-gold) !important;
  color       : var(--gold-700) !important;
  border-radius: var(--r-xs) !important;
  font-size   : 0.73rem !important;
  font-weight : 500 !important;
}
/* Sidebar reset button */
[data-testid="stSidebar"] .stButton button {
  background   : transparent !important;
  border       : 1px solid var(--border-strong) !important;
  color        : var(--text-muted) !important;
  border-radius: var(--r-sm) !important;
  font-family  : var(--font-sans) !important;
  font-size    : 0.8rem !important;
  font-weight  : 500 !important;
  height       : 36px !important;
  transition   : all 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background  : var(--stone-100) !important;
  border-color: var(--stone-400) !important;
  color       : var(--text-body) !important;
}

/* ─────────────────────────────────────────────────────────────────────
   TYPOGRAPHY — global overrides
───────────────────────────────────────────────────────────────────── */
h1,h2,h3,h4 {
  font-family   : var(--font-sans) !important;
  color         : var(--text-ink) !important;
  letter-spacing: -0.02em !important;
}
p,span,label,div,li { font-family:var(--font-sans) !important; }

[data-testid="stHeading"] h1 {
  font-size  : 1.85rem !important;
  font-weight: 700 !important;
}
[data-testid="stHeading"] h2 {
  font-size  : 1.45rem !important;
  font-weight: 700 !important;
}
[data-testid="stHeading"] h3 {
  font-size  : 1.1rem !important;
  font-weight: 600 !important;
}

/* ─────────────────────────────────────────────────────────────────────
   METRIC CARDS
───────────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background   : var(--bg-surface) !important;
  border       : 1px solid var(--border-base) !important;
  border-radius: var(--r-lg) !important;
  padding      : var(--s6) var(--s7) !important;
  box-shadow   : var(--shadow-sm) !important;
  position     : relative !important;
  overflow     : hidden !important;
  transition   : transform 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stMetric"]::after {
  content   : '';
  position  : absolute;
  bottom    : 0; left: 0; right: 0;
  height    : 2px;
  background: linear-gradient(90deg,
    var(--gold-400) 0%,
    var(--gold-300) 50%,
    transparent 100%);
  opacity   : 0;
  transition: opacity 0.2s ease;
}
[data-testid="stMetric"]:hover {
  transform : translateY(-2px) !important;
  box-shadow: var(--shadow-lg) !important;
}
[data-testid="stMetric"]:hover::after { opacity:1; }
[data-testid="stMetricLabel"] {
  font-family   : var(--font-sans) !important;
  font-size     : 0.68rem !important;
  font-weight   : 600 !important;
  color         : var(--text-faint) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--font-mono) !important;
  font-size  : 2rem !important;
  font-weight: 400 !important;
  color      : var(--stone-900) !important;
  line-height: 1.1 !important;
}
[data-testid="stMetricDelta"] > div {
  font-family: var(--font-sans) !important;
  font-size  : 0.74rem !important;
  font-weight: 500 !important;
}

/* ─────────────────────────────────────────────────────────────────────
   BUTTONS
───────────────────────────────────────────────────────────────────── */
/* Primary — gold */
button[data-testid="baseButton-primary"],
.stButton button[kind="primary"] {
  background     : var(--stone-900) !important;
  border         : 1px solid var(--stone-900) !important;
  color          : var(--stone-25) !important;
  font-family    : var(--font-sans) !important;
  font-weight    : 600 !important;
  font-size      : 0.84rem !important;
  letter-spacing : 0.02em !important;
  border-radius  : var(--r-sm) !important;
  height         : 40px !important;
  padding        : 0 22px !important;
  transition     : all 0.18s ease !important;
  box-shadow     : var(--shadow-sm) !important;
}
button[data-testid="baseButton-primary"]:hover,
.stButton button[kind="primary"]:hover {
  background: var(--stone-800) !important;
  box-shadow: var(--shadow-md) !important;
  transform : translateY(-1px) !important;
}
button[data-testid="baseButton-primary"]:active,
.stButton button[kind="primary"]:active {
  transform : translateY(0px) !important;
  background: var(--stone-950) !important;
}

/* Secondary */
button[data-testid="baseButton-secondary"],
.stButton button[kind="secondary"],
.stButton button:not([kind="primary"]) {
  background   : var(--bg-surface) !important;
  border       : 1px solid var(--border-strong) !important;
  color        : var(--text-body) !important;
  font-family  : var(--font-sans) !important;
  font-weight  : 500 !important;
  font-size    : 0.82rem !important;
  border-radius: var(--r-sm) !important;
  height       : 38px !important;
  box-shadow   : var(--shadow-xs) !important;
  transition   : all 0.15s ease !important;
}
button[data-testid="baseButton-secondary"]:hover,
.stButton button:not([kind="primary"]):hover {
  border-color: var(--accent) !important;
  color       : var(--accent-dark) !important;
  background  : var(--gold-100) !important;
  box-shadow  : var(--shadow-sm) !important;
}

/* Download */
[data-testid="stDownloadButton"] button {
  background   : var(--bg-surface) !important;
  border       : 1px solid var(--border-strong) !important;
  color        : var(--text-body) !important;
  font-family  : var(--font-sans) !important;
  font-weight  : 500 !important;
  border-radius: var(--r-sm) !important;
  height       : 40px !important;
  transition   : all 0.15s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
  border-color: var(--accent) !important;
  color       : var(--accent-dark) !important;
  background  : var(--gold-100) !important;
  box-shadow  : var(--shadow-gold) !important;
}

/* ─────────────────────────────────────────────────────────────────────
   FORM INPUTS
───────────────────────────────────────────────────────────────────── */
[data-baseweb="select"] > div,
[data-testid="stSelectbox"] > div > div {
  background   : var(--bg-surface) !important;
  border       : 1px solid var(--border-base) !important;
  border-radius: var(--r-sm) !important;
  font-family  : var(--font-sans) !important;
  font-size    : 0.875rem !important;
  color        : var(--text-ink) !important;
  box-shadow   : var(--shadow-xs) !important;
  transition   : border-color 0.15s, box-shadow 0.15s !important;
  min-height   : 40px !important;
}
[data-baseweb="select"] > div:hover { border-color: var(--stone-400) !important; }
[data-baseweb="select"] > div:focus-within {
  border-color: var(--accent) !important;
  box-shadow  : 0 0 0 3px rgba(201,168,76,0.15) !important;
}
[data-baseweb="popover"],[data-baseweb="menu"] {
  background: var(--bg-surface) !important;
}
[data-baseweb="menu"] {
  border       : 1px solid var(--border-base) !important;
  border-radius: var(--r-md) !important;
  box-shadow   : var(--shadow-xl) !important;
}
[data-baseweb="menu"] li {
  font-family: var(--font-sans) !important;
  font-size  : 0.85rem !important;
  color      : var(--text-body) !important;
  padding    : 8px 14px !important;
}
[data-baseweb="menu"] li:hover {
  background: var(--gold-100) !important;
  color     : var(--accent-dark) !important;
}
[data-baseweb="menu"] [aria-selected="true"] {
  background: var(--gold-100) !important;
  color     : var(--gold-700) !important;
  font-weight: 600 !important;
}

textarea,
[data-testid="stTextArea"] textarea {
  background   : var(--bg-surface) !important;
  border       : 1px solid var(--border-base) !important;
  border-radius: var(--r-sm) !important;
  color        : var(--text-ink) !important;
  font-family  : var(--font-sans) !important;
  font-size    : 0.875rem !important;
  line-height  : 1.65 !important;
  box-shadow   : var(--shadow-xs) !important;
  caret-color  : var(--accent) !important;
  transition   : border-color 0.15s, box-shadow 0.15s !important;
}
textarea:focus,[data-testid="stTextArea"] textarea:focus {
  border-color: var(--accent) !important;
  box-shadow  : 0 0 0 3px rgba(201,168,76,0.12) !important;
  outline     : none !important;
}
textarea::placeholder { color: var(--text-faint) !important; }

/* Field labels */
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stTextInput"] label {
  font-family   : var(--font-sans) !important;
  font-size     : 0.68rem !important;
  font-weight   : 700 !important;
  color         : var(--text-faint) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
}

/* Slider */
[data-testid="stSlider"] [data-testid="stSliderTrackFill"] { background: var(--accent) !important; }
[data-testid="stSlider"] [data-testid="stSliderThumb"] {
  background  : var(--bg-surface) !important;
  border      : 2px solid var(--accent) !important;
  box-shadow  : 0 0 0 3px rgba(201,168,76,0.2) !important;
}

/* ─────────────────────────────────────────────────────────────────────
   TABS
───────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
  background   : var(--bg-subtle) !important;
  border       : 1px solid var(--border-base) !important;
  border-radius: var(--r-sm) !important;
  padding      : 3px !important;
  gap          : 1px !important;
}
[data-testid="stTabs"] button[role="tab"] {
  background   : transparent !important;
  border       : none !important;
  color        : var(--text-muted) !important;
  font-family  : var(--font-sans) !important;
  font-size    : 0.8rem !important;
  font-weight  : 500 !important;
  border-radius: var(--r-xs) !important;
  padding      : 7px 16px !important;
  transition   : all 0.15s !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
  color     : var(--text-body) !important;
  background: rgba(255,255,255,0.7) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: var(--bg-surface) !important;
  color     : var(--text-ink) !important;
  font-weight: 600 !important;
  box-shadow : var(--shadow-sm) !important;
}

/* ─────────────────────────────────────────────────────────────────────
   EXPANDERS
───────────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
  background   : var(--bg-surface) !important;
  border       : 1px solid var(--border-base) !important;
  border-radius: var(--r-lg) !important;
  box-shadow   : var(--shadow-xs) !important;
  overflow     : hidden !important;
  margin-bottom: var(--s3) !important;
  transition   : box-shadow 0.2s, border-color 0.2s !important;
}
[data-testid="stExpander"]:hover {
  box-shadow  : var(--shadow-md) !important;
  border-color: var(--border-strong) !important;
}
[data-testid="stExpander"] summary {
  background : var(--bg-surface) !important;
  color      : var(--text-body) !important;
  font-family: var(--font-sans) !important;
  font-size  : 0.875rem !important;
  font-weight: 500 !important;
  padding    : 14px 20px !important;
}
[data-testid="stExpander"] summary:hover {
  background: var(--stone-50) !important;
  color     : var(--text-ink) !important;
}
[data-testid="stExpander"] summary svg { color: var(--accent) !important; }
[data-testid="stExpander"] > div > div {
  background: var(--bg-surface) !important;
  border-top : 1px solid var(--border-faint) !important;
  padding    : 16px 20px !important;
}

/* ─────────────────────────────────────────────────────────────────────
   DATA TABLE
───────────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border       : 1px solid var(--border-base) !important;
  border-radius: var(--r-lg) !important;
  overflow     : hidden !important;
  box-shadow   : var(--shadow-sm) !important;
}
[data-testid="stDataFrame"] table { background: white !important; }
[data-testid="stDataFrame"] th {
  background    : var(--stone-50) !important;
  color         : var(--text-faint) !important;
  font-family   : var(--font-sans) !important;
  font-size     : 0.68rem !important;
  font-weight   : 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.09em !important;
  border-bottom : 1px solid var(--border-base) !important;
  padding       : 10px 14px !important;
}
[data-testid="stDataFrame"] td {
  color      : var(--text-body) !important;
  font-family: var(--font-sans) !important;
  font-size  : 0.84rem !important;
  padding    : 9px 14px !important;
  border-color: var(--border-faint) !important;
}
[data-testid="stDataFrame"] tr:hover td {
  background: var(--gold-100) !important;
  color     : var(--text-ink) !important;
}

/* ─────────────────────────────────────────────────────────────────────
   ALERTS
───────────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: var(--r-md) !important;
  border-width : 1px !important;
  font-family  : var(--font-sans) !important;
  font-size    : 0.84rem !important;
}
[data-testid="stAlert"][kind="info"]    { background:var(--slate-50) !important;border-color:var(--slate-200) !important;color:var(--slate-700) !important; }
[data-testid="stAlert"][kind="success"] { background:var(--sage-50)  !important;border-color:var(--sage-200)  !important;color:var(--sage-700)  !important; }
[data-testid="stAlert"][kind="warning"] { background:var(--gold-100) !important;border-color:var(--border-gold) !important;color:var(--gold-700) !important; }
[data-testid="stAlert"][kind="error"]   { background:var(--rose-50)  !important;border-color:var(--rose-200)  !important;color:var(--rose-700)  !important; }

/* Captions */
[data-testid="stCaptionContainer"] p,.stCaption,small {
  color      : var(--text-faint) !important;
  font-family: var(--font-sans) !important;
  font-size  : 0.73rem !important;
}

/* Spinner */
[data-testid="stSpinner"] p {
  color      : var(--text-muted) !important;
  font-size  : 0.84rem !important;
  font-family: var(--font-sans) !important;
}

/* Charts */
[data-testid="stImage"] img {
  border-radius: var(--r-lg);
  box-shadow   : var(--shadow-sm);
}

/* ─────────────────────────────────────────────────────────────────────
   ══ CUSTOM COMPONENTS ══
───────────────────────────────────────────────────────────────────── */

/* ── TOPBAR / MASTHEAD ─────────────────────────────────────────────── */
.masthead {
  display        : flex;
  align-items    : center;
  justify-content: space-between;
  padding        : var(--s6) 0 var(--s5) 0;
  border-bottom  : 1px solid var(--border-base);
  margin-bottom  : 0;
}
.masthead-brand {
  display    : flex;
  align-items: baseline;
  gap        : var(--s2);
}
.masthead-wordmark {
  font-family   : var(--font-display);
  font-size     : 1.6rem;
  font-weight   : 600;
  color         : var(--text-ink);
  letter-spacing: -0.01em;
  font-style    : italic;
}
.masthead-wordmark span { color: var(--accent); font-style: normal; }
.masthead-rule {
  width     : 1px;
  height    : 18px;
  background: var(--border-strong);
  margin    : 0 var(--s3);
  display   : inline-block;
  vertical-align: middle;
}
.masthead-sub {
  font-family   : var(--font-sans);
  font-size     : 0.72rem;
  font-weight   : 500;
  color         : var(--text-faint);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.masthead-meta { display:flex; align-items:center; gap:var(--s3); }

/* ── STATUS / CATEGORY PILLS ───────────────────────────────────────── */
.pill {
  display       : inline-flex;
  align-items   : center;
  gap           : 5px;
  padding       : 4px 11px;
  border-radius : var(--r-xs);
  font-family   : var(--font-sans);
  font-size     : 0.7rem;
  font-weight   : 600;
  letter-spacing: 0.03em;
  white-space   : nowrap;
}
.pill-dot {
  width : 5px; height: 5px;
  border-radius: 50%;
  background   : currentColor;
}
.pill-live    { background:var(--sage-50);  color:var(--sage-600);   border:1px solid var(--sage-200); }
.pill-live .pill-dot { animation: liveblink 2s infinite; }
.pill-fresh   { background:var(--sage-50);  color:var(--sage-600);   border:1px solid var(--sage-200); }
.pill-stale   { background:var(--gold-100); color:var(--gold-700);   border:1px solid var(--border-gold); }
.pill-old     { background:var(--rose-50);  color:var(--rose-600);   border:1px solid var(--rose-200); }
.pill-unknown { background:var(--stone-100);color:var(--stone-500);  border:1px solid var(--border-base); }
.pill-stone   { background:var(--stone-100);color:var(--stone-600);  border:1px solid var(--border-base); }
.pill-gold    { background:var(--gold-100); color:var(--gold-700);   border:1px solid var(--border-gold); }
.pill-slate   { background:var(--slate-50); color:var(--slate-600);  border:1px solid var(--slate-200); }
.pill-rose    { background:var(--rose-50);  color:var(--rose-600);   border:1px solid var(--rose-200); }
.pill-sage    { background:var(--sage-50);  color:var(--sage-600);   border:1px solid var(--sage-200); }

@keyframes liveblink { 0%,100%{opacity:1;} 50%{opacity:0.25;} }

/* ── HERO BLOCK ────────────────────────────────────────────────────── */
.hero {
  padding       : var(--s16) 0 var(--s12) 0;
  border-bottom : 1px solid var(--border-base);
  margin-bottom : var(--s12);
  display       : grid;
  grid-template-columns: 1fr 320px;
  gap           : var(--s8);
  align-items   : end;
}
.hero-left {}
.hero-eyebrow {
  font-family   : var(--font-sans);
  font-size     : 0.68rem;
  font-weight   : 700;
  color         : var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.18em;
  margin-bottom : var(--s4);
  display       : flex;
  align-items   : center;
  gap           : var(--s3);
}
.hero-eyebrow::after {
  content   : '';
  width     : 32px; height: 1px;
  background: var(--accent);
  opacity   : 0.5;
}
.hero-title {
  font-family   : var(--font-display) !important;
  font-size     : 3.5rem !important;
  font-weight   : 600 !important;
  color         : var(--stone-900) !important;
  letter-spacing: -0.025em !important;
  line-height   : 1.02 !important;
  margin        : 0 0 var(--s5) 0 !important;
}
.hero-title em {
  font-style: italic;
  color     : var(--accent);
}
.hero-desc {
  font-size  : 1rem;
  color      : var(--text-body);
  line-height: 1.65;
  max-width  : 540px;
  margin     : 0 0 var(--s6) 0;
}
.hero-pills { display:flex; gap:var(--s2); flex-wrap:wrap; }
.hero-right {
  padding-bottom: var(--s2);
}
/* Stat cluster in hero */
.hero-stat-cluster {
  background   : var(--bg-surface);
  border       : 1px solid var(--border-base);
  border-radius: var(--r-xl);
  padding      : var(--s6) var(--s7);
  box-shadow   : var(--shadow-md);
  position     : relative;
  overflow     : hidden;
}
.hero-stat-cluster::before {
  content  : '';
  position : absolute;
  top:0;left:0;right:0;height:2px;
  background: linear-gradient(90deg,
    var(--gold-400) 0%,
    var(--gold-300) 60%,
    transparent 100%);
}
.hsc-row {
  display        : flex;
  justify-content: space-between;
  align-items    : center;
  padding        : var(--s3) 0;
  border-bottom  : 1px solid var(--border-faint);
}
.hsc-row:last-child { border-bottom:none; padding-bottom:0; }
.hsc-row:first-child { padding-top:0; }
.hsc-label {
  font-size     : 0.72rem;
  font-weight   : 600;
  color         : var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.hsc-value {
  font-family: var(--font-mono);
  font-size  : 1.3rem;
  font-weight: 400;
  color      : var(--text-ink);
  letter-spacing: -0.02em;
}
.hsc-delta {
  font-size  : 0.7rem;
  font-weight: 500;
  padding    : 2px 7px;
  border-radius: var(--r-xs);
}
.hsc-delta-up   { background:var(--sage-50); color:var(--sage-600); }
.hsc-delta-down { background:var(--rose-50); color:var(--rose-600); }

/* ── SECTION DIVIDER ──────────────────────────────────────────────── */
.sec-divider {
  display    : flex;
  align-items: center;
  gap        : var(--s4);
  margin     : var(--s12) 0 var(--s8) 0;
}
.sec-divider::before,
.sec-divider::after {
  content   : '';
  flex      : 1;
  height    : 1px;
  background: var(--border-base);
}
.sec-divider-inner {
  display    : flex;
  align-items: center;
  gap        : var(--s3);
  white-space: nowrap;
}
.sec-num {
  font-family   : var(--font-mono);
  font-size     : 0.65rem;
  font-weight   : 500;
  color         : var(--text-faint);
  letter-spacing: 0.08em;
}
.sec-name {
  font-family   : var(--font-sans);
  font-size     : 0.68rem;
  font-weight   : 700;
  color         : var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

/* ── SECTION HEADER ───────────────────────────────────────────────── */
.sec-head {
  margin-bottom: var(--s6);
}
.sec-head-title {
  font-family   : var(--font-sans);
  font-size     : 1.35rem;
  font-weight   : 700;
  color         : var(--text-ink);
  letter-spacing: -0.02em;
  margin        : 0 0 var(--s2) 0;
}
.sec-head-sub {
  font-size  : 0.875rem;
  color      : var(--text-muted);
  line-height: 1.5;
  font-weight: 400;
  margin     : 0;
}

/* ── SURFACE CARD ─────────────────────────────────────────────────── */
.surface {
  background   : var(--bg-surface);
  border       : 1px solid var(--border-base);
  border-radius: var(--r-lg);
  padding      : var(--s6) var(--s8);
  box-shadow   : var(--shadow-sm);
  transition   : box-shadow 0.2s, border-color 0.2s;
}
.surface:hover { box-shadow:var(--shadow-md); }
.surface-sm    { padding: var(--s5) var(--s6); }

/* accent bar */
.surface-gold::before {
  content  : '';
  position : absolute;
  top:0;left:0;width:3px;bottom:0;
  background: linear-gradient(180deg,var(--gold-400),var(--gold-200));
  border-radius: var(--r-sm) 0 0 var(--r-sm);
}
.surface-sage::before {
  content  : '';
  position : absolute;
  top:0;left:0;width:3px;bottom:0;
  background: linear-gradient(180deg,var(--sage-400),var(--sage-200));
  border-radius: var(--r-sm) 0 0 var(--r-sm);
}
.surface-slate::before {
  content  : '';
  position : absolute;
  top:0;left:0;width:3px;bottom:0;
  background: linear-gradient(180deg,var(--slate-400),var(--slate-200));
  border-radius: var(--r-sm) 0 0 var(--r-sm);
}

/* ── FIELD LABEL (inline) ─────────────────────────────────────────── */
.field-label {
  font-family   : var(--font-sans);
  font-size     : 0.65rem;
  font-weight   : 700;
  color         : var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom : var(--s2);
}

/* ── TREND BADGES ─────────────────────────────────────────────────── */
.trend-up {
  display    : inline-flex; align-items: center; gap: 4px;
  padding    : 4px 10px; border-radius: var(--r-xs);
  background : var(--sage-50); color: var(--sage-600);
  border     : 1px solid var(--sage-200);
  font-family: var(--font-sans); font-size: 0.73rem; font-weight: 600;
}
.trend-down {
  display    : inline-flex; align-items: center; gap: 4px;
  padding    : 4px 10px; border-radius: var(--r-xs);
  background : var(--rose-50); color: var(--rose-600);
  border     : 1px solid var(--rose-200);
  font-family: var(--font-sans); font-size: 0.73rem; font-weight: 600;
}
.trend-stable {
  display    : inline-flex; align-items: center; gap: 4px;
  padding    : 4px 10px; border-radius: var(--r-xs);
  background : var(--stone-100); color: var(--stone-500);
  border     : 1px solid var(--border-base);
  font-family: var(--font-sans); font-size: 0.73rem; font-weight: 600;
}

/* ── DATA ROW ─────────────────────────────────────────────────────── */
.drow {
  display        : flex;
  justify-content: space-between;
  align-items    : center;
  padding        : 9px 0;
  border-bottom  : 1px solid var(--border-faint);
  transition     : all 0.12s;
}
.drow:last-child  { border-bottom: none; }
.drow:hover       { padding-left:6px; padding-right:6px;
                    margin:0 -6px; border-radius:var(--r-xs);
                    background:var(--gold-100); }
.drow-label       { font-size:0.84rem; color:var(--text-body); }
.drow-value       { font-family:var(--font-mono); font-size:0.78rem;
                    font-weight:500; color:var(--stone-700); }
.drow-sub         { font-size:0.7rem; color:var(--text-faint); margin-left:5px; }

/* ── MINI PROGRESS BAR ────────────────────────────────────────────── */
.mbar { margin-bottom: 14px; }
.mbar-head {
  display        : flex;
  justify-content: space-between;
  align-items    : center;
  margin-bottom  : 6px;
}
.mbar-lbl { font-size:0.82rem; color:var(--text-body); font-weight:400; }
.mbar-pct { font-family:var(--font-mono); font-size:0.72rem; color:var(--text-faint); font-weight:500; }
.mbar-track { background:var(--stone-100); border-radius:99px; height:5px; overflow:hidden; }
.mbar-fill  { height:100%; border-radius:99px; transition:width 0.5s ease; }

/* ── TAGS ─────────────────────────────────────────────────────────── */
.tag {
  display      : inline-block;
  padding      : 3px 10px;
  border-radius: var(--r-xs);
  font-family  : var(--font-sans);
  font-size    : 0.72rem;
  font-weight  : 600;
  margin       : 3px;
  letter-spacing: 0.01em;
  transition   : all 0.15s;
  cursor       : default;
}
.tag:hover { transform:translateY(-1px); box-shadow:var(--shadow-sm); }
.tag-sage  { background:var(--sage-50);  color:var(--sage-700);   border:1px solid var(--sage-200); }
.tag-rose  { background:var(--rose-50);  color:var(--rose-700);   border:1px solid var(--rose-200); }
.tag-gold  { background:var(--gold-100); color:var(--gold-700);   border:1px solid var(--border-gold); }
.tag-slate { background:var(--slate-50); color:var(--slate-700);  border:1px solid var(--slate-200); }
.tag-stone { background:var(--stone-100);color:var(--stone-600);  border:1px solid var(--border-base); }

/* ── COMPANY CARD ─────────────────────────────────────────────────── */
.company-card {
  background   : var(--bg-surface);
  border       : 1px solid var(--border-base);
  border-radius: var(--r-xl);
  padding      : var(--s8) var(--s10);
  box-shadow   : var(--shadow-md);
  margin-top   : var(--s5);
  position     : relative;
  overflow     : hidden;
}
.company-card::before {
  content  : '';
  position : absolute;
  top:0;left:0;right:0;height:2px;
  background: linear-gradient(90deg,
    var(--gold-400) 0%,
    var(--gold-200) 50%,
    transparent 100%);
}
.co-name {
  font-family   : var(--font-sans);
  font-size     : 1.4rem;
  font-weight   : 700;
  color         : var(--text-ink);
  letter-spacing: -0.02em;
  margin        : 0 0 3px 0;
}
.co-meta { font-size:0.84rem; color:var(--text-faint); }

/* ── SCORE RING ───────────────────────────────────────────────────── */
.score-ring {
  width          : 144px;
  height         : 144px;
  border-radius  : 50%;
  border         : 2px solid;
  display        : flex;
  flex-direction : column;
  align-items    : center;
  justify-content: center;
  margin         : 0 auto 12px auto;
  position       : relative;
  box-shadow     : var(--shadow-lg);
  background     : var(--bg-surface);
}
.score-ring::before {
  content     : '';
  position    : absolute;
  inset       : -7px;
  border-radius: 50%;
  border      : 1px solid;
  border-color: inherit;
  opacity     : 0.18;
}
.score-num { font-family:var(--font-mono); font-size:2.4rem; font-weight:400; line-height:1; }
.score-lbl { font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-top:3px; opacity:0.65; }

/* ── SALARY RESULT ────────────────────────────────────────────────── */
.salary-result {
  background   : var(--bg-surface);
  border       : 1px solid var(--border-base);
  border-radius: var(--r-xl);
  padding      : var(--s8) var(--s10);
  box-shadow   : var(--shadow-lg);
  margin-top   : var(--s6);
  position     : relative;
  overflow     : hidden;
}
.salary-result::before {
  content  : '';
  position : absolute;
  top:0;left:0;right:0;height:2px;
  background: linear-gradient(90deg,
    var(--gold-500),var(--gold-300),var(--sage-400));
}
.sal-eyebrow {
  font-family   : var(--font-sans);
  font-size     : 0.65rem;
  font-weight   : 700;
  color         : var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.sal-role {
  font-family: var(--font-sans);
  font-size  : 1rem;
  font-weight: 600;
  color      : var(--text-ink);
  margin-top : 4px;
  letter-spacing: -0.01em;
}
.sal-conf {
  display      : inline-flex;
  align-items  : center;
  padding      : 4px 12px;
  border-radius: var(--r-xs);
  font-size    : 0.7rem;
  font-weight  : 700;
  letter-spacing: 0.04em;
}
.sal-bar-track {
  background   : var(--stone-100);
  border-radius: 99px;
  height       : 7px;
  margin       : var(--s6) 0 var(--s2) 0;
  overflow     : hidden;
}
.sal-bar-fill {
  height       : 100%;
  border-radius: 99px;
  background   : linear-gradient(90deg,var(--gold-500),var(--gold-300),var(--sage-400));
  transition   : width 0.7s cubic-bezier(0.4,0,0.2,1);
}
.sal-scale {
  display        : flex;
  justify-content: space-between;
  font-family    : var(--font-mono);
  font-size      : 0.65rem;
  color          : var(--text-faint);
}

/* ── FORM SURFACE ─────────────────────────────────────────────────── */
.form-surface {
  background   : var(--bg-surface);
  border       : 1px solid var(--border-base);
  border-radius: var(--r-xl);
  padding      : var(--s8) var(--s10);
  box-shadow   : var(--shadow-sm);
}
.form-sep {
  display      : flex;
  align-items  : center;
  gap          : var(--s3);
  margin       : var(--s6) 0 var(--s4) 0;
  font-family  : var(--font-sans);
  font-size    : 0.65rem;
  font-weight  : 700;
  color        : var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.form-sep::before,.form-sep::after {
  content: ''; flex:1; height:1px; background:var(--border-base);
}

/* ── AI CALLOUT ───────────────────────────────────────────────────── */
.ai-result {
  background   : linear-gradient(135deg,var(--gold-100) 0%,var(--stone-50) 100%);
  border       : 1px solid var(--border-gold);
  border-radius: var(--r-lg);
  padding      : var(--s6) var(--s7);
  margin-top   : var(--s4);
}
.ai-text {
  font-size  : 0.9rem;
  color      : var(--stone-800);
  line-height: 1.75;
}

/* ── EMPTY STATE ──────────────────────────────────────────────────── */
.empty {
  border       : 1.5px dashed var(--border-strong);
  border-radius: var(--r-xl);
  padding      : var(--s12) var(--s8);
  text-align   : center;
  background   : var(--stone-25);
}
.empty-icon { font-size:1.8rem; margin-bottom:var(--s3); opacity:0.35; }
.empty-txt  { font-size:0.84rem; color:var(--text-faint); font-weight:500; }

/* ── EXPORT CARD ──────────────────────────────────────────────────── */
.export-card {
  background   : var(--bg-surface);
  border       : 1px solid var(--border-base);
  border-radius: var(--r-xl);
  padding      : var(--s8);
  box-shadow   : var(--shadow-sm);
  height       : 100%;
  transition   : box-shadow 0.2s, border-color 0.2s;
}
.export-card:hover {
  box-shadow  : var(--shadow-lg);
  border-color: var(--border-gold);
}
.export-icon-box {
  width        : 38px;
  height       : 38px;
  border-radius: var(--r-sm);
  display      : flex;
  align-items  : center;
  justify-content: center;
  font-size    : 16px;
  margin-bottom: var(--s4);
  border       : 1px solid var(--border-base);
  background   : var(--stone-50);
}
.export-title { font-size:1rem; font-weight:700; color:var(--text-ink); margin:0 0 6px 0; letter-spacing:-0.01em; }
.export-desc  { font-size:0.8rem; color:var(--text-faint); margin:0 0 var(--s5) 0; line-height:1.55; }

/* ── FOOTER ───────────────────────────────────────────────────────── */
.footer {
  display        : flex;
  align-items    : center;
  justify-content: space-between;
  padding        : var(--s6) 0 var(--s8) 0;
  border-top     : 1px solid var(--border-base);
  margin-top     : var(--s12);
}
.footer-brand {
  font-family: var(--font-display);
  font-size  : 1.05rem;
  font-weight: 600;
  font-style : italic;
  color      : var(--text-ink);
}
.footer-brand span { color:var(--accent); font-style:normal; }
.footer-meta { font-size:0.72rem; color:var(--text-faint); }

/* Animations */
@keyframes fadeUp {
  from { opacity:0; transform:translateY(10px); }
  to   { opacity:1; transform:translateY(0); }
}
.fade-in { animation: fadeUp 0.4s ease both; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════════════════════
raw_df = load_data()


# ══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:28px;">
      <div style="font-family:'Cormorant Garamond',serif;font-size:1.45rem;
                  font-weight:600;font-style:italic;color:#1a1814;letter-spacing:-0.01em;
                  margin-bottom:3px;">
        JobSeek<span style="color:#c9a84c;font-style:normal;">AI</span>
      </div>
      <div style="font-family:'Outfit',sans-serif;font-size:0.65rem;font-weight:700;
                  color:#a8a398;text-transform:uppercase;letter-spacing:0.14em;">
        BD Market Intelligence
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#e5e2da;margin:0 0 22px 0;">', unsafe_allow_html=True)

    st.markdown("""
    <p style="font-family:'Outfit',sans-serif;font-size:0.65rem;font-weight:700;
              color:#a8a398;text-transform:uppercase;letter-spacing:0.12em;
              margin-bottom:14px;">Filter Data</p>
    """, unsafe_allow_html=True)

    options = get_filter_options(raw_df)
    sel_industries = st.multiselect("Industry",  options=options["industry"],  default=[])
    sel_roles      = st.multiselect("Job Role",  options=options["job_title"], default=[])
    sel_locations  = st.multiselect("Location",  options=options["location"],  default=[])

    st.markdown('<hr style="border-color:#e5e2da;margin:22px 0;">', unsafe_allow_html=True)

    if st.button("↺  Reset All Filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.markdown('<hr style="border-color:#e5e2da;margin:22px 0 14px 0;">', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-family:'Outfit',sans-serif;font-size:0.72rem;color:#a8a398;line-height:2.1;">
      <div>
        <span style="font-family:'DM Mono',monospace;color:#c9a84c;font-weight:500;">
          {len(raw_df):,}
        </span> postings indexed
      </div>
      <div>Syncs every <span style="color:#c9a84c;">60 min</span></div>
    </div>
    """, unsafe_allow_html=True)


df = apply_filters(raw_df, sel_industries, sel_roles, sel_locations)
freshness     = get_data_freshness(raw_df)
delta_jobs    = get_delta_jobs(raw_df)
jobs_today    = get_jobs_today(raw_df)
new_cos_today = get_new_companies_today(raw_df)


# ══════════════════════════════════════════════════════════════════════════
#  MASTHEAD
# ══════════════════════════════════════════════════════════════════════════
badge_cls = f"pill-{freshness['status']}"

st.markdown(f"""
<div class="masthead fade-in">
  <div class="masthead-brand">
    <span class="masthead-wordmark">JobSeek<span>AI</span></span>
    <span class="masthead-rule"></span>
    <span class="masthead-sub">Bangladesh Job Market Platform</span>
  </div>
  <div class="masthead-meta">
    <span class="pill pill-live">
      <span class="pill-dot"></span> Live
    </span>
    <span class="pill {badge_cls}">{freshness['emoji']} {freshness['last_updated']}</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  HERO  — above the fold, screenshot zone
# ══════════════════════════════════════════════════════════════════════════
if df.empty:
    st.warning("No postings match your filters. Try resetting.")
    st.stop()

delta_sign = "+" if delta_jobs >= 0 else ""
delta_cls  = "hsc-delta-up" if delta_jobs >= 0 else "hsc-delta-down"

st.markdown(f"""
<div class="hero fade-in">
  <div class="hero-left">
    <div class="hero-eyebrow">Live Market Intelligence</div>
    <h1 class="hero-title">Where Bangladesh<br>is <em>hiring</em> today</h1>
    <p class="hero-desc">
      Real-time analytics on hiring demand, salary benchmarks,
      skill gaps, and company intelligence — scraped daily from BDJobs.com
      and enriched by AI.
    </p>
    <div class="hero-pills">
      <span class="pill pill-stone">BDJobs.com</span>
      <span class="pill pill-gold">AI-Powered</span>
      <span class="pill pill-slate">Daily Scrape</span>
    </div>
  </div>
  <div class="hero-right">
    <div class="hero-stat-cluster">
      <div class="hsc-row">
        <span class="hsc-label">Total Postings</span>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="hsc-value">{len(df):,}</span>
          <span class="hsc-delta {delta_cls}">{delta_sign}{delta_jobs}d</span>
        </div>
      </div>
      <div class="hsc-row">
        <span class="hsc-label">Companies Hiring</span>
        <span class="hsc-value">{df['company'].nunique():,}</span>
      </div>
      <div class="hsc-row">
        <span class="hsc-label">Industries Active</span>
        <span class="hsc-value">{df['industry'].nunique()}</span>
      </div>
      <div class="hsc-row">
        <span class="hsc-label">Cities Covered</span>
        <span class="hsc-value">{df['location'].nunique()}</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# KPI row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Postings",    f"{len(df):,}",
              delta=f"+{jobs_today} today" if jobs_today > 0 else "—",
              delta_color="normal" if jobs_today > 0 else "off")
with c2:
    st.metric("Hiring Companies",  f"{df['company'].nunique():,}",
              delta=f"+{new_cos_today} new" if new_cos_today > 0 else None,
              delta_color="normal")
with c3:
    st.metric("Industries Active", f"{df['industry'].nunique()}")
with c4:
    st.metric("Cities Covered",    f"{df['location'].nunique()}")


# ══════════════════════════════════════════════════════════════════════════
#  § 01  MARKET OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">01</span>
    <span class="sec-name">Market Overview</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Industry & Location Distribution</p>
  <p class="sec-head-sub">How active job demand spreads across sectors and geographies</p>
</div>
""", unsafe_allow_html=True)

cl, cr = st.columns(2)
with cl: st.pyplot(plot_industry_distribution(df))
with cr: st.pyplot(plot_location_distribution(df))


# ══════════════════════════════════════════════════════════════════════════
#  § 02  TOP HIRING COMPANIES
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">02</span>
    <span class="sec-name">Hiring Leaders</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Top Hiring Companies</p>
  <p class="sec-head-sub">Organisations with the highest volume of live postings</p>
</div>
""", unsafe_allow_html=True)

st.pyplot(plot_top_companies(df, top_n=12))


# ══════════════════════════════════════════════════════════════════════════
#  § 03  POSTING TREND
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">03</span>
    <span class="sec-name">Temporal Analysis</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Posting Trend</p>
  <p class="sec-head-sub">Daily posting volume — spotting acceleration and slowdowns</p>
</div>
""", unsafe_allow_html=True)

fig_trend = plot_posting_trend(df)
if fig_trend:
    st.pyplot(fig_trend)
else:
    st.markdown("""
    <div class="empty">
      <div class="empty-icon">📈</div>
      <p class="empty-txt">Trend chart appears after multiple days of data collection</p>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  § 04  LIVE FEED
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">04</span>
    <span class="sec-name">Live Feed</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Active Job Listings</p>
  <p class="sec-head-sub">All postings matching your current filter selection</p>
</div>
""", unsafe_allow_html=True)

display_cols = ["job_title","company","industry","location"]
if "date_scraped" in df.columns: display_cols.append("date_scraped")

st.dataframe(
    df[display_cols].rename(columns={
        "job_title":"Job Title","company":"Company",
        "industry":"Industry","location":"Location","date_scraped":"Posted",
    }),
    use_container_width=True, hide_index=True, height=420,
)


# ══════════════════════════════════════════════════════════════════════════
#  § 05  EDUCATION & EXPERIENCE
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">05</span>
    <span class="sec-name">Qualification Intelligence</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Education & Experience Demand</p>
  <p class="sec-head-sub">What qualifications and seniority levels the market is asking for</p>
</div>
""", unsafe_allow_html=True)

t1, t2, t3 = st.tabs(["Degree Demand", "Experience Levels", "Industry × Education"])

with t1:
    dc = get_degree_counts(df)
    if dc.empty:
        st.markdown('<div class="empty"><div class="empty-icon">🎓</div><p class="empty-txt">No degree data yet</p></div>', unsafe_allow_html=True)
    else:
        st.pyplot(plot_degree_demand(dc))
        top = dc.iloc[0]
        st.success(f"Most demanded: **{top['Degree']}** — {top['Count']} postings ({top['Count']/len(df)*100:.1f}%)")
        with st.expander("View full breakdown"):
            st.dataframe(dc, use_container_width=True, hide_index=True)

with t2:
    ec = get_experience_level_counts(df)
    if ec.empty or ec["Count"].sum() == 0:
        st.markdown('<div class="empty"><div class="empty-icon">💼</div><p class="empty-txt">No experience data yet</p></div>', unsafe_allow_html=True)
    else:
        st.pyplot(plot_experience_levels(ec))
        tot = ec["Count"].sum()
        for _, row in ec.iterrows():
            pct = row["Count"]/tot*100
            ic = "🟡" if row["Level"].startswith("Entry") else ("🔵" if row["Level"].startswith("Mid") else "🟣")
            st.caption(f"{ic}  **{row['Level']}** — {row['Count']} jobs ({pct:.1f}%)")
        with st.expander("View table"):
            st.dataframe(ec, use_container_width=True, hide_index=True)

with t3:
    mx = get_industry_education_matrix(df)
    if mx.empty:
        st.markdown('<div class="empty"><div class="empty-icon">🔥</div><p class="empty-txt">Insufficient cross-reference data yet</p></div>', unsafe_allow_html=True)
    else:
        st.caption("Darker = more postings requiring that degree in that industry")
        st.pyplot(plot_industry_education_heatmap(mx))
        with st.expander("View raw matrix"):
            st.dataframe(mx, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
#  § 06  COMPANY INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">06</span>
    <span class="sec-name">Company Intelligence</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Company Hiring Profiles</p>
  <p class="sec-head-sub">Deep-dive into any company — open roles, locations, experience mix, and weekly trend</p>
</div>
""", unsafe_allow_html=True)

if "selected_company" not in st.session_state:
    st.session_state.selected_company = None

top_cos = get_top_companies_list(df, n=8)
st.markdown("""
<p style="font-family:'Outfit',sans-serif;font-size:0.65rem;font-weight:700;
          color:#a8a398;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:10px;">
  Quick select — top 8</p>
""", unsafe_allow_html=True)

btn_cols = st.columns(len(top_cos))
for i, co in enumerate(top_cos):
    with btn_cols[i]:
        if st.button(co, key=f"qbtn_{i}", use_container_width=True):
            st.session_state.selected_company = co

all_companies = sorted(df["company"].dropna().unique().tolist())
sel_dd = st.selectbox("Search any company",
                      ["— Search a company —"] + all_companies,
                      index=0, key="company_dropdown")
if not sel_dd.startswith("—"):
    st.session_state.selected_company = sel_dd

if st.session_state.selected_company:
    company = st.session_state.selected_company
    intel   = get_company_intel(company, df)

    if intel.get("error"):
        st.error(intel["error"])
    else:
        trend = intel["trend"]
        if trend == "up":
            t_html = f'<span class="trend-up">↑ +{intel["trend_delta"]} this week</span>'
        elif trend == "down":
            t_html = f'<span class="trend-down">↓ −{intel["trend_delta"]} this week</span>'
        elif trend == "stable":
            t_html = '<span class="trend-stable">→ Stable</span>'
        else:
            t_html = '<span class="trend-stable">· No trend data</span>'

        st.markdown(f"""
        <div class="company-card fade-in">
          <div style="display:flex;justify-content:space-between;
                      align-items:flex-start;flex-wrap:wrap;gap:14px;">
            <div>
              <p class="co-name">{company}</p>
              <p class="co-meta">{" · ".join(intel["industries"])}</p>
            </div>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
              {t_html}
              <span class="pill pill-stone" style="font-family:'DM Mono',monospace;">
                {intel["total_openings"]} open
              </span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Open Positions", intel["total_openings"])
        k2.metric("Top Role", (intel["top_role"][:22]+"…") if len(intel["top_role"])>22 else intel["top_role"])
        k3.metric("Primary Location", intel["top_location"])
        k4.metric("Sectors", len(intel["industries"]))

        if trend == "up":
            st.success(f"↑  {company} posted {intel['recent_count']} jobs this week — up from {intel['prev_count']} last week")
        elif trend == "down":
            st.warning(f"↓  {company} posted {intel['recent_count']} jobs this week — down from {intel['prev_count']} last week")
        elif trend == "stable":
            st.info(f"→  {intel['recent_count']} jobs posted this week — consistent with last week")

        st.markdown('<hr style="margin:24px 0 20px 0;">', unsafe_allow_html=True)

        c_roles, c_locs, c_exp = st.columns(3)

        with c_roles:
            st.markdown('<p class="field-label">Roles Hiring</p>', unsafe_allow_html=True)
            for _, row in intel["role_breakdown"].iterrows():
                pct = row["Count"] / intel["total_openings"] * 100
                st.markdown(f"""
                <div class="drow">
                  <span class="drow-label">{str(row["Role"])[:34]}</span>
                  <span>
                    <span class="drow-value">{int(row["Count"])}</span>
                    <span class="drow-sub">({pct:.0f}%)</span>
                  </span>
                </div>""", unsafe_allow_html=True)

        with c_locs:
            st.markdown('<p class="field-label">Locations</p>', unsafe_allow_html=True)
            for _, row in intel["location_breakdown"].iterrows():
                pct = row["Count"] / intel["total_openings"] * 100
                st.markdown(f"""
                <div class="drow">
                  <span class="drow-label">{str(row["Location"])[:28]}</span>
                  <span>
                    <span class="drow-value" style="color:var(--sage-600);">{int(row["Count"])}</span>
                    <span class="drow-sub">({pct:.0f}%)</span>
                  </span>
                </div>""", unsafe_allow_html=True)

        with c_exp:
            st.markdown('<p class="field-label">Experience Mix</p>', unsafe_allow_html=True)
            eb = intel["exp_breakdown"]
            if not eb.empty and eb["Count"].sum() > 0:
                total_co = eb["Count"].sum()
                bar_colors = {
                    "Entry Level (0–2 yrs)": ("var(--sage-400)",  "var(--sage-100)"),
                    "Mid Level (3–5 yrs)":   ("var(--gold-500)",  "var(--gold-200)"),
                    "Senior Level (6+ yrs)": ("var(--slate-400)", "var(--slate-100)"),
                }
                for _, row in eb.iterrows():
                    if row["Count"] == 0: continue
                    pct = row["Count"] / total_co * 100
                    fill, bg = bar_colors.get(row["Level"], ("var(--stone-400)","var(--stone-100)"))
                    st.markdown(f"""
                    <div class="mbar">
                      <div class="mbar-head">
                        <span class="mbar-lbl">{row["Level"]}</span>
                        <span class="mbar-pct">{pct:.0f}%</span>
                      </div>
                      <div class="mbar-track" style="background:{bg};">
                        <div class="mbar-fill" style="width:{pct:.0f}%;background:{fill};"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("No experience data for this company.")

        st.markdown("")
        with st.expander(f"View all {intel['total_openings']} open positions at {company}"):
            st.dataframe(intel["all_jobs"], use_container_width=True, hide_index=True)
else:
    st.markdown("""
    <div class="empty" style="margin-top:16px;">
      <div class="empty-icon">🏢</div>
      <p class="empty-txt">Select a company above to view its intelligence profile</p>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  § 07  AI MARKET INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">07</span>
    <span class="sec-name">AI Intelligence</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Market Summary <span style="font-size:0.7rem;font-weight:700;
    color:#c9a84c;text-transform:uppercase;letter-spacing:0.1em;
    vertical-align:middle;margin-left:8px;">AI</span></p>
  <p class="sec-head-sub">Executive brief generated from your filtered dataset by Groq LLM</p>
</div>
""", unsafe_allow_html=True)

if st.button("Generate Market Summary", type="primary", use_container_width=True):
    with st.spinner("Analysing market patterns …"):
        top_sk   = top_skills_list(df, n=10)
        top_role = most_common_value(df["job_title"])
        top_ind  = most_common_value(df["industry"])
        metrics  = {"mean":None,"median":None,"min":None,"max":None,"count":0}
        summary  = generate_market_summary(top_sk, metrics, top_role, top_ind)
    st.markdown(f'<div class="ai-result"><p class="ai-text">{summary}</p></div>',
                unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="empty" style="padding:32px 24px;">
      <div class="empty-icon">◆</div>
      <p class="empty-txt">Click to generate an AI market brief from current data</p>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  § 08  JOB RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">08</span>
    <span class="sec-name">AI Matching</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Personalised Job Recommendations <span style="font-size:0.7rem;font-weight:700;
    color:#c9a84c;text-transform:uppercase;letter-spacing:0.1em;
    vertical-align:middle;margin-left:8px;">AI</span></p>
  <p class="sec-head-sub">Describe your background — AI surfaces your best-fit roles from live listings</p>
</div>
""", unsafe_allow_html=True)

with st.form("rec_form"):
    user_profile_rec = st.text_area(
        "Your Skills & Experience",
        placeholder="Example: 2 years Python and data analysis, Pandas, SQL, Power BI. BSc CSE. Targeting data roles in Dhaka.",
        height=130,
    )
    ca, cb = st.columns([3,1])
    with cb: top_n = st.selectbox("Results", [3,5,7], index=1)
    sub_rec = st.form_submit_button("Find My Best Matches", type="primary", use_container_width=True)

if sub_rec:
    if not user_profile_rec.strip():
        st.warning("Please enter your skills and experience first.")
    else:
        with st.spinner("Scanning live listings …"):
            recs = generate_job_recommendations(user_profile_rec, df, top_n=top_n)
        if not recs:
            st.error("No recommendations returned. Please try again.")
        elif "error" in recs[0]:
            st.error(recs[0]["error"])
        else:
            st.success(f"Found your top {len(recs)} matches")
            st.markdown("")
            for rec in recs:
                score = rec["match_score"]
                lbl   = "Strong Match" if score>=80 else ("Good Match" if score>=60 else "Partial Match")
                with st.expander(f"#{rec['rank']}  {rec['job_title']} @ {rec['company']}  ·  {score}/100  {lbl}",
                                 expanded=(rec["rank"]==1)):
                    m1,m2,m3 = st.columns(3)
                    m1.metric("Location", rec["location"])
                    m2.metric("Industry", rec["industry"])
                    m3.metric("Match",    f"{score}/100")
                    st.markdown(f"**Why this fits:** {rec['reason']}")
                    if rec.get("experience") and rec["experience"] not in ("N/A","nan",""):
                        st.caption(f"Skills/Info: {rec['experience']}")
                    if rec.get("deadline") and rec["deadline"] not in ("N/A","nan",""):
                        st.caption(f"Deadline: {rec['deadline']}")
            st.caption("Tip: Apply sidebar filters before searching for tighter matches.")


# ══════════════════════════════════════════════════════════════════════════
#  § 09  SKILL GAP ANALYZER
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">09</span>
    <span class="sec-name">Skill Intelligence</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Skill Gap Analyzer <span style="font-size:0.7rem;font-weight:700;
    color:#c9a84c;text-transform:uppercase;letter-spacing:0.1em;
    vertical-align:middle;margin-left:8px;">AI</span></p>
  <p class="sec-head-sub">Compare your profile against live demand — see exactly what's missing and how to close it</p>
</div>
""", unsafe_allow_html=True)

with st.form("gap_form"):
    user_profile_gap = st.text_area(
        "Your Current Skills & Background",
        placeholder="Example: 1 year Python and basic SQL, Excel, some data analysis. BSc CSE from Dhaka.",
        height=140,
    )
    sub_gap = st.form_submit_button("Analyze My Skill Gaps", type="primary", use_container_width=True)

if sub_gap:
    if not user_profile_gap.strip():
        st.warning("Please describe your background first.")
    else:
        with st.spinner("Comparing against live market demand …"):
            gap_result = analyze_skill_gap(user_profile_gap, df)
        if gap_result.get("error"):
            st.error(gap_result["error"])
        else:
            score       = int(gap_result.get("readiness_score", 50))
            score_label = gap_result.get("score_label", "")
            score_color = gap_result.get("score_color", "#c9a84c")

            st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)
            ring_col, sum_col = st.columns([1,2])

            with ring_col:
                st.markdown(f"""
                <div class="score-ring"
                     style="border-color:{score_color};color:{score_color};
                            box-shadow:0 0 28px {score_color}20;">
                  <span class="score-num">{score}</span>
                  <span class="score-lbl">Market Fit</span>
                </div>
                <p style="text-align:center;font-family:'Outfit',sans-serif;
                           font-size:0.65rem;font-weight:700;
                           color:var(--text-faint);text-transform:uppercase;
                           letter-spacing:0.12em;margin-top:4px;">{score_label}</p>
                """, unsafe_allow_html=True)

            with sum_col:
                st.markdown(f"""
                <div style="padding-left:12px;">
                  <p class="field-label" style="margin-bottom:10px;">Your Market Position</p>
                  <p style="font-size:0.9rem;color:var(--text-body);line-height:1.75;
                             margin-bottom:18px;">{gap_result.get("summary","")}</p>
                """, unsafe_allow_html=True)
                top_roles_gap = gap_result.get("top_roles",[])
                if top_roles_gap:
                    st.markdown('<p class="field-label" style="margin-bottom:8px;">Best-fit roles right now</p>', unsafe_allow_html=True)
                    st.markdown(
                        " ".join(f'<span class="tag tag-slate">{r}</span>' for r in top_roles_gap),
                        unsafe_allow_html=True
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)
            cm, cs, co = st.columns(3)

            with cm:
                st.markdown('<p class="field-label">✓ Skills You Have</p>', unsafe_allow_html=True)
                matched = gap_result.get("matched_skills",[])
                if matched:
                    st.markdown(" ".join(f'<span class="tag tag-sage">{s}</span>' for s in matched), unsafe_allow_html=True)
                else:
                    st.caption("No direct market matches found yet.")

            with cs:
                st.markdown('<p class="field-label">★ Your Strengths</p>', unsafe_allow_html=True)
                strengths = gap_result.get("strengths",[])
                if strengths:
                    st.markdown(" ".join(f'<span class="tag tag-slate">{s}</span>' for s in strengths), unsafe_allow_html=True)
                else:
                    st.caption("Build more experience to surface strengths.")

            with co:
                st.markdown('<p class="field-label">○ Nice-to-Have</p>', unsafe_allow_html=True)
                optional = gap_result.get("missing_optional",[])
                if optional:
                    st.markdown(" ".join(f'<span class="tag tag-gold">{s}</span>' for s in optional), unsafe_allow_html=True)
                else:
                    st.success("No significant optional gaps.")

            st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)
            st.markdown('<p class="field-label" style="margin-bottom:14px;">Critical Gaps — Learning Roadmap</p>', unsafe_allow_html=True)

            missing_critical = gap_result.get("missing_critical",[])
            if not missing_critical:
                st.success("No critical gaps — your profile aligns well with current demand.")
            else:
                for i, gap in enumerate(missing_critical):
                    with st.expander(f"Gap {i+1} — {gap.get('skill','Unknown')}", expanded=(i==0)):
                        g1, g2 = st.columns(2)
                        with g1:
                            st.markdown(f'<p class="field-label">Why This Matters</p><p style="font-size:0.86rem;color:var(--text-body);line-height:1.65;">{gap.get("reason","")}</p>', unsafe_allow_html=True)
                        with g2:
                            st.markdown(f'<p class="field-label">How To Learn (Free)</p><p style="font-size:0.86rem;color:var(--text-body);line-height:1.65;">{gap.get("how_to_learn","")}</p>', unsafe_allow_html=True)

            st.markdown('<hr style="margin:16px 0;">', unsafe_allow_html=True)
            nm = len(gap_result.get("matched_skills",[]));nc = len(gap_result.get("missing_critical",[]));no = len(gap_result.get("missing_optional",[]))
            tot = nm+nc+no
            if tot > 0:
                r1,r2,r3 = st.columns(3)
                r1.metric("Skills Matched", nm,  delta=f"{nm/tot*100:.0f}% of tracked", delta_color="normal")
                r2.metric("Critical Gaps",  nc,  delta="High priority" if nc>0 else "None", delta_color="inverse" if nc>0 else "normal")
                r3.metric("Optional Gaps",  no,  delta_color="off")
            st.caption("Tip: Filter to a specific industry for sector-targeted analysis.")


# ══════════════════════════════════════════════════════════════════════════
#  § 10  SALARY ESTIMATOR
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">10</span>
    <span class="sec-name">Compensation Intelligence</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">AI Salary Estimator <span style="font-size:0.7rem;font-weight:700;
    color:#c9a84c;text-transform:uppercase;letter-spacing:0.1em;
    vertical-align:middle;margin-left:8px;">AI</span></p>
  <p class="sec-head-sub">Realistic BDT salary range for any role — grounded in live BDJobs market data</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="form-surface">', unsafe_allow_html=True)
with st.form("salary_form"):
    st.markdown('<div class="form-sep">Role Details</div>', unsafe_allow_html=True)
    fr1, fr2 = st.columns(2)
    with fr1:
        jt_list = sorted(raw_df["job_title"].dropna().unique().tolist())
        sel_jt  = st.selectbox("Job Title",  ["— Select a role —"]+jt_list, index=0)
    with fr2:
        in_list = sorted(raw_df["industry"].dropna().unique().tolist())
        sel_ind = st.selectbox("Industry",   ["— Select an industry —"]+in_list, index=0)

    st.markdown('<div class="form-sep">Location & Experience</div>', unsafe_allow_html=True)
    fl1, fl2, fl3 = st.columns(3)
    with fl1:
        lo_list = sorted(raw_df["location"].dropna().unique().tolist())
        sel_loc = st.selectbox("Location",         ["— Select a location —"]+lo_list, index=0)
    with fl2:
        sel_lvl = st.selectbox("Experience Level", [
            "— Select level —",
            "Entry Level (0–2 years)","Mid Level (3–5 years)",
            "Senior Level (6–10 years)","Expert / Lead (10+ years)",
        ], index=0)
    with fl3:
        sel_yrs = st.slider("Years of Experience", 0, 20, 2, 1)

    st.markdown('<div class="form-sep">Education</div>', unsafe_allow_html=True)
    sel_edu = st.selectbox("Highest Education Level", [
        "— Select education —",
        "SSC / O-Level","HSC / A-Level","Diploma",
        "Bachelor's (BSc / BA / BBA / B.Eng)",
        "Master's (MSc / MBA / MA)","PhD / Doctorate",
        "Professional Certification (no degree)",
    ], index=0)

    st.markdown("")
    sub_sal = st.form_submit_button("Estimate My Salary", type="primary", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

if sub_sal:
    errs = []
    if sel_jt.startswith("—"):  errs.append("Select a Job Title.")
    if sel_ind.startswith("—"): errs.append("Select an Industry.")
    if sel_loc.startswith("—"): errs.append("Select a Location.")
    if sel_lvl.startswith("—"): errs.append("Select Experience Level.")
    if sel_edu.startswith("—"): errs.append("Select Education Level.")
    for e in errs: st.warning(f"⚠  {e}")

    if not errs:
        with st.spinner("Calculating salary estimate …"):
            sal = estimate_salary(
                job_title=sel_jt, industry=sel_ind, experience_level=sel_lvl,
                years_of_experience=sel_yrs, location=sel_loc, education=sel_edu, df=df,
            )
        if sal.get("error"):
            st.error(sal["error"])
        else:
            mn=sal["min_salary"]; med=sal["median_salary"]; mx=sal["max_salary"]
            conf=sal.get("confidence","Medium")
            fill=min(int(med/300_000*100),100)

            # confidence pill colours
            c_map = {
                "High":   ("var(--sage-50)","var(--sage-700)","var(--sage-200)"),
                "Medium": ("var(--gold-100)","var(--gold-700)","var(--border-gold)"),
                "Low":    ("var(--rose-50)","var(--rose-700)","var(--rose-200)"),
            }
            cbg,cfg,cbd = c_map.get(conf,("var(--stone-100)","var(--stone-600)","var(--border-base)"))

            st.markdown('<div class="salary-result fade-in">', unsafe_allow_html=True)

            hc1, hc2 = st.columns([3,1])
            with hc1:
                st.markdown(f"""
                <p class="sal-eyebrow">Estimated Monthly Salary · BDT</p>
                <p class="sal-role">{sel_jt} · {sel_ind} · {sel_loc}</p>
                """, unsafe_allow_html=True)
            with hc2:
                st.markdown(f"""
                <div style="text-align:right;padding-top:10px;">
                  <span class="sal-conf"
                    style="background:{cbg};color:{cfg};border:1px solid {cbd};">
                    {conf} Confidence
                  </span>
                </div>""", unsafe_allow_html=True)

            st.markdown("")
            s1,s2,s3 = st.columns(3)
            s1.metric("Minimum / month",          f"৳ {mn:,}")
            s2.metric("Median / month (likely)",   f"৳ {med:,}")
            s3.metric("Maximum / month",           f"৳ {mx:,}")

            st.markdown(f"""
            <div class="sal-bar-track">
              <div class="sal-bar-fill" style="width:{fill}%;"></div>
            </div>
            <div class="sal-scale">
              <span>৳ 0</span><span>৳ 1,00,000</span>
              <span>৳ 2,00,000</span><span>৳ 3,00,000+</span>
            </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("")

            i1,i2,i3 = st.columns(3)
            with i1:
                st.markdown('<p class="field-label">Why This Estimate</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size:0.86rem;color:var(--text-body);line-height:1.7;">{sal.get("reasoning","")}</p>', unsafe_allow_html=True)
            with i2:
                st.markdown('<p class="field-label">Market Context</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size:0.86rem;color:var(--text-body);line-height:1.7;">{sal.get("market_context","")}</p>', unsafe_allow_html=True)
            with i3:
                st.markdown('<p class="field-label">Negotiation Tips</p>', unsafe_allow_html=True)
                for tip in sal.get("negotiation_tips",[]):
                    st.markdown(f'<p style="font-size:0.86rem;color:var(--text-body);margin:0 0 6px;line-height:1.6;">· {tip}</p>', unsafe_allow_html=True)

            st.markdown('<hr style="margin:18px 0;">', unsafe_allow_html=True)
            fu,fd = st.columns(2)
            with fu:
                st.markdown('<p class="field-label">Factors → Higher Salary</p>', unsafe_allow_html=True)
                for f in sal.get("factors_up",[]):
                    st.markdown(f'<span class="tag tag-sage">↑ {f}</span>', unsafe_allow_html=True)
            with fd:
                st.markdown('<p class="field-label">Factors → Lower Salary</p>', unsafe_allow_html=True)
                for f in sal.get("factors_down",[]):
                    st.markdown(f'<span class="tag tag-rose">↓ {f}</span>', unsafe_allow_html=True)

            st.markdown("")
            st.caption("AI estimate based on Bangladesh market norms and live BDJobs data. Actual salaries vary by company and negotiation.")


# ══════════════════════════════════════════════════════════════════════════
#  § 11  EXPORT
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-divider">
  <div class="sec-divider-inner">
    <span class="sec-num">11</span>
    <span class="sec-name">Export</span>
  </div>
</div>
<div class="sec-head">
  <p class="sec-head-title">Download Data</p>
  <p class="sec-head-sub">Export filtered listings as CSV or generate a formatted PDF market report</p>
</div>
""", unsafe_allow_html=True)

active_filters = {"industries":sel_industries,"roles":sel_roles,"locations":sel_locations}
today_str = datetime.now().strftime("%Y-%m-%d")

ec1, ec2 = st.columns(2)
with ec1:
    st.markdown(f"""
    <div class="export-card">
      <div class="export-icon-box">📊</div>
      <p class="export-title">CSV Spreadsheet</p>
      <p class="export-desc">
        Export all <strong>{len(df):,} filtered postings</strong> as a CSV.
        Opens directly in Excel or Google Sheets.
      </p>
    </div>""", unsafe_allow_html=True)
    st.download_button(
        "↓  Download CSV", data=to_csv_bytes(df),
        file_name=f"jobseekAI_{today_str}.csv",
        mime="text/csv", use_container_width=True,
    )
    st.caption(f"{len(df):,} rows · UTF-8 encoded")

with ec2:
    st.markdown("""
    <div class="export-card">
      <div class="export-icon-box">📄</div>
      <p class="export-title">PDF Market Report</p>
      <p class="export-desc">
        Formatted report with KPIs, company rankings,
        industry breakdown, and job listings.
      </p>
    </div>""", unsafe_allow_html=True)
    if st.button("↓  Generate PDF Report", use_container_width=True, key="pdf_btn"):
        with st.spinner("Building PDF …"):
            try:
                pdf_bytes = to_pdf_bytes(df, active_filters)
                st.download_button("↓  Save PDF", data=pdf_bytes,
                                   file_name=f"jobseekAI_report_{today_str}.pdf",
                                   mime="application/pdf",
                                   use_container_width=True, type="primary")
                st.success("PDF ready.")
            except Exception as e:
                st.error(f"Could not generate PDF: {e}")
    st.caption("KPIs · Top 10 rankings · First 30 listings")


# ══════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="footer">
  <div class="footer-brand">
    JobSeek<span>AI</span>
  </div>
  <div class="footer-meta">
    Live data from BDJobs.com · Auto-updated daily ·
    Built with Streamlit & Python · {datetime.now().year}
  </div>
</div>
""", unsafe_allow_html=True)
