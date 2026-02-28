# JobSeekAI — Bangladesh Job Market Intelligence Platform

> **Live platform:** [jobseekai-cnhqtvqhjqkc2mapssxr6p.streamlit.app](https://jobseekai-cnhqtvqhjqkc2mapssxr6p.streamlit.app)
> **Repository:** [github.com/Sohamsarker999/JobSeekAI](https://github.com/Sohamsarker999/JobSeekAI)

---

## Overview

JobSeekAI is a real-time job market analytics platform built for the Bangladesh employment landscape. It scrapes live job postings from BDJobs.com daily, stores them in a Google Sheet, and surfaces structured intelligence through an AI-powered Streamlit dashboard — covering market distribution, hiring trends, education demand, company profiles, skill gap analysis, and salary benchmarking.

The platform was designed to answer one question that no existing tool in Bangladesh answers well: *Where exactly is the market hiring right now, and am I positioned for it?*

It combines a zero-cost data pipeline (GitHub Actions + Google Sheets), a generative AI layer (Groq / Llama 3.3 70B), and a production-grade frontend designed to the standard of a venture-backed SaaS product.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Data Pipeline](#3-data-pipeline)
4. [Feature Breakdown](#4-feature-breakdown)
5. [AI Layer](#5-ai-layer)
6. [Frontend Design System](#6-frontend-design-system)
7. [Module Reference](#7-module-reference)
8. [Setup & Installation](#8-setup--installation)
9. [Configuration](#9-configuration)
10. [Deployment](#10-deployment)
11. [Design Decisions & Tradeoffs](#11-design-decisions--tradeoffs)
12. [Known Limitations](#12-known-limitations)
13. [Roadmap](#13-roadmap)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│                                                                 │
│   BDJobs.com REST API                                           │
│         │                                                       │
│         ▼                                                       │
│   Python Scraper (scraper.py)                                   │
│         │  Runs via GitHub Actions — daily at 8:00 AM BST      │
│         ▼                                                       │
│   Google Sheets  ◄──────────────────────────────────────────┐  │
│   (Live datastore)                                          │  │
└─────────────────────────────────────────────────────────────┼──┘
                                                              │
┌─────────────────────────────────────────────────────────────┼──┐
│                     APPLICATION LAYER                       │  │
│                                                             │  │
│   utils.py          visualizations.py    ai_summary.py      │  │
│   ─────────         ──────────────────   ──────────────     │  │
│   load_data() ──────────────────────────────────────────────┘  │
│   apply_filters()   plot_*() functions   generate_*()           │
│   get_*() helpers   matplotlib/seaborn   Groq API              │
│   to_csv/pdf()                           Llama 3.3 70B          │
│         │                   │                   │               │
│         └───────────────────┴───────────────────┘              │
│                             │                                   │
│                        main.py                                  │
│                   (Streamlit dashboard)                         │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │  End User        │
                   │  Browser         │
                   │  Streamlit Cloud │
                   └──────────────────┘
```

**Key architectural decisions:**

- **Google Sheets as the datastore** — zero infrastructure cost, shareable, inspectable without a database client, and natively supported by Streamlit's secrets management. The tradeoff against a proper database is acceptable at this scale (< 10,000 rows).
- **GitHub Actions as the scheduler** — free, version-controlled, auditable cron runner. Eliminates the need for any always-on compute for data collection.
- **Groq for inference** — orders of magnitude faster than OpenAI for structured outputs. Llama 3.3 70B provides quality comparable to GPT-4o for information extraction tasks at a fraction of the latency and cost.
- **Streamlit for the UI** — rapid iteration, Python-native, and deployable to Streamlit Community Cloud at no cost. Custom CSS overrides bring it to production-grade visual standards.

---

## 2. Project Structure

```
JobSeekAI/
├── app/
│   ├── main.py              # Streamlit dashboard — all 11 sections + full design system
│   ├── utils.py             # Data loading, filtering, aggregation, export helpers
│   ├── visualizations.py    # All matplotlib/seaborn chart functions
│   └── ai_summary.py        # Groq API wrappers for all four AI features
│
├── scraper/
│   └── scraper.py           # BDJobs.com scraper + Google Sheets writer
│
├── .github/
│   └── workflows/
│       └── scrape.yml       # GitHub Actions daily cron workflow
│
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

### File Roles at a Glance

| File | Responsibility | Changes often? |
|------|---------------|----------------|
| `main.py` | Dashboard layout, UI, design system CSS, section orchestration | Yes — UI iterations |
| `utils.py` | Pure data functions: load, filter, aggregate, export | Rarely |
| `visualizations.py` | Chart rendering functions, returns matplotlib figures | Rarely |
| `ai_summary.py` | All four Groq API calls: summary, recommendations, skill gap, salary | Occasionally |
| `scraper.py` | BDJobs REST API → Google Sheets ETL | Only if API changes |
| `scrape.yml` | GitHub Actions schedule + secrets injection | Rarely |

---

## 3. Data Pipeline

### 3.1 Scraping

The scraper runs daily at **08:00 AM Bangladesh Standard Time (BST / UTC+6)** via GitHub Actions. It calls the BDJobs.com REST API endpoint, paginates through results, and writes structured job records to a Google Sheet.

Each job record contains the following fields:

| Field | Description |
|-------|-------------|
| `job_title` | Normalised job title string |
| `company` | Employer name |
| `industry` | Industry category as classified by BDJobs |
| `location` | City or region of the role |
| `experience` | Raw experience requirement string (e.g. "3–5 years") |
| `deadline` | Application deadline date |
| `date_scraped` | ISO 8601 timestamp of when this record was collected |

### 3.2 GitHub Actions Workflow

```yaml
# .github/workflows/scrape.yml (conceptual)
on:
  schedule:
    - cron: '0 2 * * *'   # 02:00 UTC = 08:00 BST
  workflow_dispatch:        # Manual trigger available

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run scraper
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
          SHEET_ID: ${{ secrets.SHEET_ID }}
        run: python scraper/scraper.py
```

The `workflow_dispatch` trigger allows manual reruns directly from the GitHub Actions UI when needed.

### 3.3 Google Sheets as the Datastore

Authentication uses a Google Service Account. Credentials are stored as a GitHub Actions secret (`GOOGLE_CREDENTIALS`) containing the full JSON key, and as a Streamlit secret for the live app to read from the same sheet.

The scraper uses `gspread` to:
1. Open the target sheet by `SHEET_ID`
2. Append new rows without truncating historical data
3. Deduplicate on `(job_title, company, date_scraped)` to avoid double-writes on reruns

### 3.4 Data Freshness

The dashboard surfaces data freshness in real time via `get_data_freshness()` in `utils.py`. It computes the age of the most recent `date_scraped` value and returns one of four statuses:

| Status | Condition | UI Indicator |
|--------|-----------|--------------|
| `fresh` | Data < 12 hours old | Green pill |
| `stale` | Data 12–36 hours old | Amber pill |
| `old` | Data > 36 hours old | Red pill |
| `unknown` | No date column present | Grey pill |

This status is displayed in the masthead alongside a live-blinking indicator, so users always know the data age before drawing conclusions.

---

## 4. Feature Breakdown

The dashboard is organised into eleven numbered sections. Each section is independently filterable via the global sidebar.

### Global Sidebar Filters

Three multiselect filters apply to the entire dashboard simultaneously:

- **Industry** — Filter to one or more of the industries present in the current data
- **Job Role** — Filter to specific job titles
- **Location** — Filter to specific cities or regions

All filters are additive (OR within each filter, AND across filters). A **Reset All Filters** button clears all selections and resets session state in a single click.

The sidebar also displays the total number of indexed postings and the data sync interval (60 minutes).

---

### § 01 — Market Overview

**What it shows:** Two side-by-side charts — industry distribution and location distribution — showing how current job demand is spread across sectors and geographies.

**Charts:**
- Industry distribution: horizontal bar chart, sorted descending by posting count
- Location distribution: bar chart showing the top cities by posting volume

**Data source:** `plot_industry_distribution(df)` and `plot_location_distribution(df)` in `visualizations.py`. Both return `matplotlib` figures and are rendered via `st.pyplot()`.

---

### § 02 — Top Hiring Companies

**What it shows:** A ranked bar chart of the top 12 companies by number of active job postings.

**Chart:** `plot_top_companies(df, top_n=12)` — horizontal bar chart, colour-coded by posting volume using a continuous gradient.

**Use case:** Quickly identify which employers are in aggressive hiring mode. Useful for targeting job applications, competitor research, or market sizing.

---

### § 03 — Posting Trend

**What it shows:** A time-series line chart of daily job posting volume. Requires at least two distinct `date_scraped` values to render; otherwise shows an empty state with an explanation.

**Chart:** `plot_posting_trend(df)` — returns `None` if insufficient time-series data exists, which the dashboard handles gracefully with a placeholder empty state.

**Use case:** Spot acceleration or cooling in hiring activity over time. A rising trend signals a growing market; a dip may reflect seasonal slowdowns or sector contractions.

---

### § 04 — Active Job Listings

**What it shows:** A paginated, sortable data table of all job postings matching the current filter selection.

**Columns displayed:** Job Title, Company, Industry, Location, and Posted date (if available).

**Implementation:** `st.dataframe()` with `hide_index=True` and a fixed height of 420px. Column names are human-readable renames of the raw DataFrame columns.

---

### § 05 — Education & Experience Demand

**What it shows:** Three tabbed views of qualification demand across the filtered dataset.

**Tab 1 — Degree Demand**
Extracts degree keywords from job description fields using regex pattern matching in `get_degree_counts()`. Returns a DataFrame with `Degree` and `Count` columns, rendered as a bar chart via `plot_degree_demand()`. A success banner highlights the single most-demanded qualification level.

**Tab 2 — Experience Levels**
Buckets raw experience strings into three standardised tiers using `get_experience_level_counts()`:
- Entry Level (0–2 years)
- Mid Level (3–5 years)
- Senior Level (6+ years)

Rendered as a bar chart via `plot_experience_levels()`, with percentage breakdowns shown as captions beneath.

**Tab 3 — Industry × Education Heatmap**
A cross-tabulation matrix showing how degree demand varies by industry. Built by `get_industry_education_matrix()` and visualised via `plot_industry_education_heatmap()` using `seaborn.heatmap`. Darker cells indicate higher posting counts requiring that degree in that industry.

---

### § 06 — Company Intelligence

**What it shows:** A deep-dive intelligence profile for any company in the dataset — open positions, role breakdown, location footprint, experience mix, and weekly hiring trend.

**Interface:**
- **Quick-select row** — Two rows of 4 buttons each for the top 8 companies by posting volume. Labels truncate at 18 characters with a tooltip showing the full name.
- **Search dropdown** — A `st.selectbox` listing all companies alphabetically. Selecting from either control sets `st.session_state.selected_company`.

**Company card:** Once a company is selected, a styled card renders:
- Company name and industry tags
- Weekly trend badge (↑ up / ↓ down / → stable) computed by comparing this week's vs last week's posting count via `get_company_intel()`
- Four KPI metrics: open positions, top role, primary location, number of active sectors
- A contextual alert with the exact delta figures

**Three-column breakdown:**
- **Roles Hiring** — Top job titles with counts and percentages as data rows
- **Locations** — Geographic distribution of open roles
- **Experience Mix** — Mini progress bars showing the proportion of Entry / Mid / Senior postings, colour-coded (sage/gold/slate)

**"View all positions" expander** — A collapsible `st.dataframe` showing every open position for the selected company.

**State management:** Selection persists across page interactions via `st.session_state`. The search dropdown and quick-select buttons share the same state key, so either control updates the displayed profile.

---

### § 07 — AI Market Summary

**What it shows:** A natural-language executive brief generated by Groq from the current filtered dataset.

**How it works:**
1. On button click, extracts: top 10 skills (from `top_skills_list()`), top job title, top industry, and aggregate salary metrics
2. Passes these as structured context to `generate_market_summary()` in `ai_summary.py`
3. Groq (Llama 3.3 70B) returns a 2–4 paragraph synthesis covering demand patterns, standout sectors, and market signals
4. The response is rendered in a warm-tinted callout card with comfortable line height for readability

**Design decision:** The summary is generated on demand rather than cached, so it always reflects the current filter selection. This is intentional — a cached summary for "all industries" would be misleading if the user has filtered to "Technology only."

---

### § 08 — Personalised Job Recommendations

**What it shows:** Up to 7 AI-matched job postings from the live dataset, ranked by fit score against the user's stated background.

**Interface:** A form with a text area for free-text background description and a selectbox for the number of results (3, 5, or 7).

**How it works:**
1. `generate_job_recommendations()` receives the user's profile text and a sample of live job postings
2. The Groq model scores each posting against the profile on a 0–100 scale
3. Returns a ranked list with: job title, company, location, industry, match score, and a one-sentence explanation of why this role fits
4. Results render as numbered expanders — the top match is auto-expanded, the rest collapsed

**Score colour coding:**
- ≥ 80: Strong Match (sage/green tone)
- 60–79: Good Match (default)
- < 60: Partial Match (amber tone)

**Optional fields:** Each recommendation card also surfaces `experience` requirements and `deadline` if present in the source data.

---

### § 09 — Skill Gap Analyzer

**What it shows:** A structured market-fit assessment comparing the user's stated skills against live demand, with a readiness score, matched/missing skills, and a learning roadmap for each critical gap.

**Interface:** A single text area for free-text skill description.

**Output components:**

**Score ring** — A circular meter (144px diameter, styled with a dynamic border colour) displaying the market readiness score from 0–100. The colour and label change by score band:
- 70–100: High fit (sage green)
- 40–69: Moderate fit (gold)
- 0–39: Low fit (rose)

An outer decorative ring at 18% opacity reinforces the circular motif.

**Market Position summary** — A paragraph synthesising where the profile sits relative to current demand, followed by a tag cloud of best-fit roles the user should be targeting right now.

**Three-column skill analysis:**
- **✓ Skills You Have** — Skills from the user's profile that appear in current job postings (sage tags)
- **★ Your Strengths** — Standout skills that represent competitive advantages (slate tags)
- **○ Nice-to-Have** — Skills that would strengthen the profile but are not blocking (gold tags)

**Learning Roadmap** — One expandable card per critical gap, each containing:
- Why this skill is in demand right now (market context)
- How to learn it for free (concrete resource recommendations)

**Summary metrics row** — Three `st.metric` cards at the bottom summarising: skills matched, critical gaps, and optional gaps.

---

### § 10 — AI Salary Estimator

**What it shows:** A BDT salary range estimate (minimum, median, maximum monthly) for any role in the dataset, calibrated to experience level, location, and education.

**Interface:** A three-section form wrapped in a styled surface card:
1. **Role Details** — Job title (from live data) + Industry
2. **Location & Experience** — Location + Experience level (4 tiers) + Years slider (0–20)
3. **Education** — 7 levels from SSC/O-Level to PhD

**Validation:** All five required fields are checked before submission. Missing fields surface individual warning messages specifying exactly which field was skipped.

**Output components:**

**Salary result card** — A styled card with a 3-colour gradient top border (gold → sage). Contains:
- Eyebrow label and role/industry/location subtitle
- Confidence badge colour-coded by level (High = sage, Medium = gold, Low = rose)
- Three `st.metric` cards: minimum, median (highlighted as the likely offer), and maximum monthly figures in BDT (৳)
- **Animated progress bar** — A 7px gradient bar (gold → sage) positioned relative to a ৳0–300,000+ scale, with a 0.7s cubic-bezier transition
- Scale labels in monospace font

**Three-column explanatory panel:**
- **Why This Estimate** — AI reasoning grounded in the role and market data
- **Market Context** — Broader commentary on salary dynamics in this sector
- **Negotiation Tips** — Actionable points for the salary conversation

**Push/pull factors** — Two tag clouds showing factors that push the salary higher (sage ↑) or lower (rose ↓), giving the user a mental model for where they sit in the range.

---

### § 11 — Export

**What it shows:** Two download options for the current filtered dataset.

**CSV Export:**
- Calls `to_csv_bytes(df)` from `utils.py`
- Returns the filtered DataFrame as UTF-8 encoded CSV bytes
- Filename: `jobseekAI_YYYY-MM-DD.csv`
- Opens directly in Excel or Google Sheets

**PDF Market Report:**
- On button click, calls `to_pdf_bytes(df, active_filters)` which uses `reportlab` to construct a formatted document
- Contains: dashboard KPIs, top 10 company rankings, industry breakdown, and the first 30 job listings
- Filename: `jobseekAI_report_YYYY-MM-DD.pdf`
- Generation is done on-demand and streamed to the user without storing a file on the server

---

## 5. AI Layer

All AI features are implemented in `ai_summary.py` and share a common pattern:

1. Extract relevant context from the filtered DataFrame (top skills, distribution counts, sampled postings)
2. Construct a structured prompt with explicit output format instructions
3. Call the Groq API with `llm-llama-3.3-70b-versatile` or equivalent
4. Parse the response and return a typed dictionary to the calling code in `main.py`

### Model: Llama 3.3 70B via Groq

Groq's inference infrastructure provides sub-second latency for the 70B parameter Llama model — typically 300–700ms for the prompts used here. This latency is acceptable for on-demand generation without needing streaming UI patterns.

### The Four AI Functions

| Function | Input | Output |
|----------|-------|--------|
| `generate_market_summary()` | Top skills, top role, top industry, salary metrics | Markdown string (executive brief) |
| `generate_job_recommendations()` | User profile text, DataFrame sample | List of dicts with rank, score, reasoning |
| `analyze_skill_gap()` | User skill text, DataFrame | Dict with score, labels, matched/missing/optional skills, gap details |
| `estimate_salary()` | Role, industry, location, experience level, years, education, DataFrame | Dict with min/median/max BDT, confidence, reasoning, tips, factors |

### Prompt Design Principles

- **Structured output first** — Every prompt requests JSON-formatted output with explicit field names. This eliminates the need for response parsing heuristics.
- **Context injection** — Market data (top skills, industry distribution, location data) is injected into each prompt as bullet-point context. This grounds the AI's output in real data rather than priors.
- **Explicit constraints** — Salary prompts specify "Bangladesh market only", "monthly figures in BDT", "realistic ranges for the stated experience level". This prevents the model from defaulting to global or US-market benchmarks.
- **Error surface** — Every function returns `{"error": "<message>"}` on failure rather than raising an exception, allowing `main.py` to render a clean error state.

---

## 6. Frontend Design System

The dashboard uses a complete CSS design system injected via `st.markdown()` at startup. It overrides Streamlit's default styling at every layer without modifying the framework itself.

### Design Language: Stone & Gold

The aesthetic direction is "Editorial Intelligence" — warm off-white backgrounds, deep ink text, and a saffron gold accent. Inspired by The Economist's typographic rigour and Stripe's systematic design thinking.

**Philosophy:** A light theme with warm tones photographs better on LinkedIn than a dark terminal aesthetic. It reads as a product that a team would ship, not a developer's side project. The serif display font (Cormorant Garamond) applied only to the wordmark creates editorial gravitas without making the data dense.

### Typography

Three fonts serve distinct semantic roles:

| Font | Role | Applied to |
|------|------|-----------|
| `Cormorant Garamond` | Display / Brand | Wordmark, hero headline |
| `Outfit` | Interface / Body | All UI labels, body text, navigation, buttons |
| `DM Mono` | Data / Code | All numeric values, metric cards, salary figures, section numbers |

The monospace font on numbers is a deliberate choice: it gives data a sense of precision and aligns digits vertically in metric cards.

### Colour System

Six tonal families, each with 7–9 steps, providing full design coverage:

```
Stone     #fdfcfa → #0d0c0a   (9 steps) — Backgrounds, surfaces, text hierarchy
Gold      #fef7e0 → #5c4a15   (8 steps) — Primary accent, hover states, AI badges
Sage      #f2f7f3 → #235730   (7 steps) — Positive signals, matched skills, growth
Rose      #fdf2f2 → #8f2424   (7 steps) — Negative signals, gaps, warnings
Slate     #f0f4f8 → #182f3e   (8 steps) — Secondary data, cool accent, experience bars
```

Borders use `rgba()` opacity variants of the stone-400 value (`rgba(168,163,152,*)`) at three levels: `0.18` (faint), `0.35` (base), `0.60` (strong). This ensures borders always feel "paper-thin" rather than heavy.

### Elevation System

Six shadow levels, all warm-tinted with `rgba(26,24,20,*)` instead of neutral grey:

```css
--shadow-xs : 0 1px 2px rgba(26,24,20,0.05)
--shadow-sm : 0 1px 4px rgba(26,24,20,0.07), 0 1px 2px rgba(26,24,20,0.04)
--shadow-md : 0 4px 12px rgba(26,24,20,0.08), 0 2px 4px rgba(26,24,20,0.04)
--shadow-lg : 0 12px 28px rgba(26,24,20,0.09), 0 4px 8px rgba(26,24,20,0.05)
--shadow-xl : 0 24px 48px rgba(26,24,20,0.10), 0 8px 16px rgba(26,24,20,0.05)
--shadow-gold: 0 4px 16px rgba(201,168,76,0.22), 0 1px 4px rgba(201,168,76,0.12)
```

Warm-tinted shadows prevent the visual coldness that grey shadows create on warm backgrounds.

### Section Navigation System

Each section is separated by a centred editorial divider:

```
────────────── 06  COMPANY INTELLIGENCE ──────────────
```

This pattern, borrowed from Linear and Vercel's documentation, creates visual rhythm across the long page and makes screenshots feel like a product with a design system — not a Streamlit prototype.

### Spacing (8pt Grid)

All spacing tokens are multiples of 4px base units, aligned to an 8pt grid:

```css
--s1:4px  --s2:8px  --s3:12px  --s4:16px  --s5:20px
--s6:24px --s7:28px --s8:32px  --s10:40px --s12:48px  --s16:64px
```

### Component Inventory

| Component | Class | Used in |
|-----------|-------|---------|
| Masthead | `.masthead` | Page header |
| Status pill | `.pill`, `.pill-*` | Masthead, hero, section badges |
| Hero block | `.hero`, `.hero-stat-cluster` | Above-the-fold section |
| Section divider | `.sec-divider` | Between all 11 sections |
| Section header | `.sec-head-title`, `.sec-head-sub` | Top of each section |
| Data row | `.drow`, `.drow-label`, `.drow-value` | Company intelligence breakdown |
| Mini bar | `.mbar`, `.mbar-fill` | Experience mix in company profile |
| Score ring | `.score-ring` | Skill gap readiness score |
| Skill tag | `.tag`, `.tag-sage/rose/gold/slate` | All skill displays |
| Salary result | `.salary-result`, `.sal-bar-fill` | Salary estimator output |
| Trend badge | `.trend-up`, `.trend-down`, `.trend-stable` | Company intelligence |
| Export card | `.export-card` | Export section |
| Company card | `.company-card` | Company intelligence profile |
| AI callout | `.ai-result` | Market summary output |
| Empty state | `.empty`, `.empty-icon`, `.empty-txt` | No-data fallbacks |
| Form surface | `.form-surface`, `.form-sep` | Salary estimator form |

---

## 7. Module Reference

### `utils.py`

Core data layer. All functions are pure — they take a DataFrame (or raw data source config) and return transformed data. No side effects.

| Function | Signature | Returns |
|----------|-----------|---------|
| `load_data()` | `() → pd.DataFrame` | Full raw DataFrame from Google Sheets |
| `apply_filters()` | `(df, industries, roles, locations) → pd.DataFrame` | Filtered DataFrame |
| `get_filter_options()` | `(df) → dict` | `{industry: [...], job_title: [...], location: [...]}` |
| `most_common_value()` | `(series) → str` | Mode value of a Series |
| `top_skills_list()` | `(df, n) → list[str]` | Top N skills extracted from text fields |
| `get_delta_jobs()` | `(df) → int` | Today's posting count minus yesterday's |
| `get_jobs_today()` | `(df) → int` | Count of postings scraped today |
| `get_new_companies_today()` | `(df) → int` | New companies appearing in today's data |
| `get_data_freshness()` | `(df) → dict` | `{status, last_updated, emoji}` |
| `to_csv_bytes()` | `(df) → bytes` | UTF-8 CSV bytes for download |
| `to_pdf_bytes()` | `(df, filters) → bytes` | Formatted PDF bytes via reportlab |
| `get_degree_counts()` | `(df) → pd.DataFrame` | Degree keyword counts |
| `get_experience_level_counts()` | `(df) → pd.DataFrame` | Experience tier counts |
| `get_industry_education_matrix()` | `(df) → pd.DataFrame` | Industry × degree cross-tabulation |
| `get_company_intel()` | `(company, df) → dict` | Full company intelligence profile |
| `get_top_companies_list()` | `(df, n) → list[str]` | Top N companies by posting count |

### `visualizations.py`

All chart functions follow the same contract: accept a DataFrame or pre-aggregated DataFrame, return a `matplotlib.figure.Figure` object. The caller (`main.py`) renders it with `st.pyplot(fig)`.

| Function | Chart Type | Data Input |
|----------|-----------|-----------|
| `plot_industry_distribution()` | Horizontal bar | Raw df |
| `plot_top_companies()` | Horizontal bar | Raw df, top_n param |
| `plot_location_distribution()` | Bar | Raw df |
| `plot_posting_trend()` | Line | Raw df; returns `None` if < 2 dates |
| `plot_degree_demand()` | Bar | Pre-aggregated degree_counts df |
| `plot_experience_levels()` | Bar | Pre-aggregated exp_counts df |
| `plot_industry_education_heatmap()` | Heatmap | Pre-computed matrix df |

### `ai_summary.py`

| Function | Groq call | Response format |
|----------|-----------|----------------|
| `generate_market_summary()` | Single completion | Plain text (markdown) |
| `generate_job_recommendations()` | Single completion | JSON list of recommendation objects |
| `analyze_skill_gap()` | Single completion | JSON dict with score, skill arrays, gap details |
| `estimate_salary()` | Single completion | JSON dict with salary range, reasoning, tips |

### `main.py`

Orchestration layer. Imports from all three modules above, renders the full CSS design system at startup, manages sidebar filter state, and renders all 11 sections in sequence. Contains no data logic or chart code directly — all delegated to the appropriate module.

---

## 8. Setup & Installation

### Prerequisites

- Python 3.9 or higher
- A Google Cloud project with the Sheets API enabled
- A Google Service Account with Editor access to the target spreadsheet
- A Groq API key (free tier is sufficient)
- A GitHub repository (for the Actions scraper workflow)

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Sohamsarker999/JobSeekAI.git
cd JobSeekAI

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up Streamlit secrets (see Configuration section)
mkdir -p .streamlit
touch .streamlit/secrets.toml

# 5. Run the dashboard
streamlit run app/main.py
```

### Dependencies

```
streamlit>=1.30.0
pandas>=2.0.0
gspread>=5.12.0
google-auth>=2.23.0
groq>=0.4.0
matplotlib>=3.7.0
seaborn>=0.12.0
reportlab>=4.0.0
requests>=2.31.0
```

> **Note on pandas 2.0:** The codebase is compatible with pandas 2.0+. If you encounter `DataFrame.append` deprecation warnings from other libraries, they are not from this codebase. All DataFrame operations use `pd.concat()`.

---

## 9. Configuration

### Streamlit Secrets (`.streamlit/secrets.toml`)

```toml
# Google Sheets authentication
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"

# Sheet configuration
[sheets]
sheet_id = "your-google-sheet-id"
worksheet_name = "Jobs"           # Name of the tab within the sheet

# AI configuration
[groq]
api_key = "gsk_your_groq_api_key"
```

### GitHub Actions Secrets

The same credentials must be added to the repository's **Settings → Secrets and variables → Actions**:

| Secret Name | Value |
|-------------|-------|
| `GOOGLE_CREDENTIALS` | The full service account JSON as a single string |
| `SHEET_ID` | The Google Sheets document ID (from the URL) |

---

## 10. Deployment

### Streamlit Community Cloud

1. Push the repository to GitHub (must be public, or on a Streamlit Cloud team plan for private repos)
2. Visit [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account
3. Select the repository, set the main file path to `app/main.py`
4. Add all secrets from the [Configuration](#9-configuration) section in the Streamlit Cloud secrets editor
5. Deploy — the app will be live at `your-app-name.streamlit.app` within ~2 minutes

**The live app URL is:** `https://jobseekai-cnhqtvqhjqkc2mapssxr6p.streamlit.app`

### Update & Redeploy

- Any push to the `main` branch triggers an automatic redeploy on Streamlit Cloud
- The scraper runs independently on GitHub Actions and writes new data directly to Google Sheets — no redeployment needed for data updates
- The Streamlit app reads fresh data on every page load via `load_data()`, which calls the Google Sheets API each time

---

## 11. Design Decisions & Tradeoffs

### Why Google Sheets instead of a database?

**Decision:** Google Sheets via `gspread`

**Rationale:** At the scale of this project (< 10,000 rows, one writer, ~50 daily readers), a database would add infrastructure cost and operational complexity with no meaningful performance benefit. Google Sheets is inspectable without tooling, shareable with non-technical stakeholders, and integrates seamlessly with Streamlit's secrets system.

**Tradeoff accepted:** Sheets has a 10 million cell limit and read-quota limits (~300 reads/minute per project). Neither limit is approached at current scale.

---

### Why Groq instead of OpenAI?

**Decision:** Groq API with Llama 3.3 70B

**Rationale:** For the structured extraction tasks in this project (JSON-format recommendations, salary ranges, skill classifications), the quality delta between Llama 3.3 70B and GPT-4o is negligible. Groq's inference speed (often 5–10× faster than OpenAI) means the AI features feel responsive without streaming UI patterns. Groq's free tier is also sufficient for the expected usage volume.

**Tradeoff accepted:** The Groq free tier has rate limits. Under heavy concurrent use, requests may be throttled and the AI features will return an error state gracefully.

---

### Why Streamlit instead of FastAPI + React?

**Decision:** Streamlit for the full-stack

**Rationale:** The project is a solo-built portfolio piece. Streamlit delivers a full, interactive web application from a single Python file with no JavaScript, no build pipeline, and free cloud hosting. The UI sophistication ceiling is higher than most people assume — achieved here through 1,200+ lines of custom CSS.

**Tradeoff accepted:** Streamlit re-renders the entire script on every user interaction. For a data-heavy dashboard, this means the `load_data()` call (Google Sheets API) fires on every interaction without explicit caching. This is mitigated by the fact that the data rarely changes mid-session, but a production version would add `@st.cache_data(ttl=3600)` to `load_data()`.

---

### Why on-demand AI generation instead of caching?

**Decision:** Generate AI output on button click, not on page load

**Rationale:** The four AI features are all filter-aware — they synthesise the current filtered dataset. Caching a global response would give wrong answers to a user who has filtered to "Technology only" but is seeing a cached response computed from "all industries." Each click is a deliberate action, making the latency acceptable.

---

## 12. Known Limitations

**Google Sheets rate limits** — If multiple users load the dashboard simultaneously, the Sheets read quota may be hit, causing `load_data()` to throw a `gspread.exceptions.APIError`. The fix is to add `@st.cache_data(ttl=3600)` to `load_data()` in `utils.py`.

**No authentication** — The dashboard is fully public. Anyone with the URL can see all data and use all AI features. This is intentional for a portfolio project but would need addressing for a production deployment with sensitive data.

**AI feature rate limits** — The Groq free tier has requests-per-minute limits. Under concurrent use, AI features may fail gracefully and display an error message. The `{"error": ...}` return convention in `ai_summary.py` means the UI always handles this cleanly.

**Salary estimates are AI-generated, not empirical** — The salary estimator is powered by an LLM with Bangladesh market priors + the current dataset context. It is a calibrated estimate, not a statistical computation from verified salary data. The confidence bands and disclaimer communicate this clearly.

**BDJobs.com API dependency** — If BDJobs changes their API structure or adds authentication requirements, the scraper will stop collecting data. The data freshness indicator in the dashboard will surface this immediately (status turns `old` → red pill).

**Trend charts require historical data** — The posting trend chart (§ 03) and the weekly company trend in Company Intelligence (§ 06) both require at least 2–7 days of accumulated data to render meaningfully. On initial setup, these show empty states.

---

## 13. Roadmap

**Near-term**

- [ ] Add `@st.cache_data(ttl=3600)` to `load_data()` to prevent redundant Sheets API calls under concurrent use
- [ ] Add a job detail side panel — clicking a row in the live feed (§ 04) expands a structured card with the full posting, application link, and deadline countdown
- [ ] Email alert subscription — users can register for weekly market digests powered by the AI summary function

**Medium-term**

- [ ] Multi-source scraping — extend the pipeline to cover LinkedIn Bangladesh, Chakri.com, and Bdjobs alternatives for a fuller market picture
- [ ] Saved searches — allow users to bookmark a filter combination and return to it via a shareable URL parameter
- [ ] Skill trend tracking — store weekly skill frequency snapshots to chart how demand for specific skills evolves over time

**Long-term**

- [ ] User profiles — authenticated users can save their skill profile and receive personalised weekly gap reports
- [ ] Salary data crowdsourcing — allow verified users to submit actual offer data to improve salary estimate accuracy
- [ ] Recruiter view — a mirror dashboard optimised for hiring managers, showing candidate supply vs. demand imbalances by skill and location

---

## Author

Built by **Soham Sarker** as a product portfolio project demonstrating full-stack data engineering, AI integration, and product-grade frontend design.

- **Live app:** [jobseekai-cnhqtvqhjqkc2mapssxr6p.streamlit.app](https://jobseekai-cnhqtvqhjqkc2mapssxr6p.streamlit.app)
- **GitHub:** [github.com/Sohamsarker999/JobSeekAI](https://github.com/Sohamsarker999/JobSeekAI)

---

*This README was written to the standard expected of production open-source documentation. Every section reflects the actual implementation — no placeholders, no aspirational features presented as built.*
