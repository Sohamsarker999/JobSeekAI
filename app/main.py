"""
main.py — JobSeekAI: Bangladesh Job Market Analytics Dashboard

Entry point for the Streamlit application.
Run with:  streamlit run app/main.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="JobSeekAI — BD Job Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ai_summary import generate_market_summary  # noqa: E402
from utils import (  # noqa: E402
    apply_filters,
    get_filter_options,
    load_data,
    most_common_value,
    top_skills_list,
)
from visualizations import (  # noqa: E402
    plot_industry_distribution,
    plot_top_companies,
    plot_location_distribution,
    plot_posting_trend,
    plot_experience_distribution,
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
    }
    hr { margin: 2rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

raw_df = load_data()


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/parse-from-clipboard.png",
        width=48,
    )
    st.title("JobSeekAI")
    st.caption("Bangladesh Job Market Intelligence")
    st.markdown("---")

    st.subheader("🔎 Filters")

    options = get_filter_options(raw_df)

    sel_industries = st.multiselect(
        "Industry",
        options=options["industry"],
        default=[],
        help="Leave empty to include all industries.",
    )
    sel_roles = st.multiselect(
        "Job Role",
        options=options["job_title"],
        default=[],
        help="Leave empty to include all roles.",
    )
    sel_locations = st.multiselect(
        "Location",
        options=options["location"],
        default=[],
        help="Leave empty to include all locations.",
    )

    st.markdown("---")

    if st.button("🔄 Reset Filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    st.caption(f"Dataset: **{len(raw_df)}** postings loaded")
    st.caption("🔄 Data refreshes every hour from BDJobs")


# Apply filters
df = apply_filters(raw_df, sel_industries, sel_roles, sel_locations)

# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    """
    # 📊 JobSeekAI — Bangladesh Job Market Dashboard
    Live analytics on job demand, hiring trends, and AI-powered market
    intelligence from **{count}** job postings scraped from BDJobs.
    """.format(count=len(df))
)
st.markdown("---")

if df.empty:
    st.warning(
        "No postings match your current filter selection. "
        "Try broadening your criteria or resetting filters."
    )
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
# KEY METRICS
# ═══════════════════════════════════════════════════════════════════════════

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Postings", f"{len(df)}")
with col2:
    st.metric("Unique Companies", df["company"].nunique())
with col3:
    st.metric("Industries", df["industry"].nunique())
with col4:
    st.metric("Locations", df["location"].nunique())

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 1  INDUSTRY & LOCATION OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

st.header("🏢 Market Overview")

col_left, col_right = st.columns(2)

with col_left:
    fig_industry = plot_industry_distribution(df)
    st.pyplot(fig_industry)

with col_right:
    fig_location = plot_location_distribution(df)
    st.pyplot(fig_location)

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 2  TOP HIRING COMPANIES
# ═══════════════════════════════════════════════════════════════════════════

st.header("🏆 Top Hiring Companies")

fig_companies = plot_top_companies(df, top_n=12)
st.pyplot(fig_companies)

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 3  EXPERIENCE & EDUCATION REQUIREMENTS
# ═══════════════════════════════════════════════════════════════════════════

st.header("🎓 Requirements Analysis")

tab_exp, tab_trend = st.tabs(["Experience Requirements", "Posting Trend"])

with tab_exp:
    fig_exp = plot_experience_distribution(df)
    if fig_exp:
        st.pyplot(fig_exp)
    else:
        st.info("Experience data will appear as more jobs are scraped.")

with tab_trend:
    fig_trend = plot_posting_trend(df)
    if fig_trend:
        st.pyplot(fig_trend)
    else:
        st.info("Trend data will appear after multiple days of scraping.")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 4  JOB LISTINGS TABLE
# ═══════════════════════════════════════════════════════════════════════════

st.header("📋 Recent Job Listings")

display_cols = ["job_title", "company", "industry", "location"]
if "date_scraped" in df.columns:
    display_cols.append("date_scraped")

st.dataframe(
    df[display_cols].rename(
        columns={
            "job_title": "Job Title",
            "company": "Company",
            "industry": "Industry",
            "location": "Location",
            "date_scraped": "Posted",
        }
    ),
    use_container_width=True,
    hide_index=True,
    height=400,
)

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 5  AI MARKET INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

st.header("🤖 AI Market Intelligence")
st.caption("Powered by Groq LLM — insights generated from your filtered data")

if st.button("Generate Market Summary", type="primary", use_container_width=True):
    with st.spinner("Analysing market data with AI …"):
        top_sk = top_skills_list(df, n=10)
        top_role = most_common_value(df["job_title"])
        top_ind = most_common_value(df["industry"])

        # Pass empty salary metrics since we don't have salary data
        metrics = {"mean": None, "median": None, "min": None, "max": None, "count": 0}
        summary = generate_market_summary(top_sk, metrics, top_role, top_ind)

    st.markdown(summary)
else:
    st.info(
        "Click **Generate Market Summary** to get an AI-powered executive "
        "brief based on the currently filtered data."
    )


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption(
    "**JobSeekAI** · Built with Streamlit · Live data from BDJobs.com · "
    "Auto-updated daily"
)
