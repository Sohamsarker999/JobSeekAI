"""
main.py — JobSeekAI: Bangladesh Job Market Analytics Dashboard

Entry point for the Streamlit application.
Run with:  streamlit run app/main.py
"""

from __future__ import annotations

import sys
import os

# Ensure sibling modules (utils, visualizations, ai_summary) are importable
# when Streamlit Cloud runs this file from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="JobSeekAI — BD Job Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Now import local modules (after set_page_config)
from ai_summary import generate_market_summary  # noqa: E402
from utils import (  # noqa: E402
    add_avg_salary_column,
    apply_filters,
    calculate_salary_metrics,
    clean_skills,
    get_filter_options,
    load_data,
    most_common_value,
    skill_frequency,
    top_skills_list,
)
from visualizations import (  # noqa: E402
    plot_salary_by_role,
    plot_salary_distribution,
    plot_skill_frequency,
)

# ---------------------------------------------------------------------------
# Custom CSS for subtle polish
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Tighten metric cards */
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
    }
    /* Section dividers */
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
# SIDEBAR — FILTERS
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
        # Clear filter widget state by rerunning with no selections
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    st.caption(f"Dataset: **{len(raw_df)}** postings loaded")


# Apply filters
df = apply_filters(raw_df, sel_industries, sel_roles, sel_locations)

# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    """
    # 📊 JobSeekAI — Bangladesh Job Market Dashboard
    Real-time analytics on skills demand, salary trends, and AI-powered market
    intelligence from **{count}** job postings.
    """.format(count=len(df))
)
st.markdown("---")

# Guard: empty dataset after filtering
if df.empty:
    st.warning(
        "No postings match your current filter selection. "
        "Try broadening your criteria or resetting filters."
    )
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
# KEY METRICS
# ═══════════════════════════════════════════════════════════════════════════

df = add_avg_salary_column(df)
metrics = calculate_salary_metrics(df)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Postings", f"{len(df)}")
with col2:
    st.metric(
        "Avg Salary",
        f"৳{metrics['mean']:,.0f}" if metrics["mean"] else "N/A",
    )
with col3:
    st.metric(
        "Median Salary",
        f"৳{metrics['median']:,.0f}" if metrics["median"] else "N/A",
    )
with col4:
    st.metric("Unique Roles", df["job_title"].nunique())

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 1  SKILL FREQUENCY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

st.header("🛠️ Skill Demand Analysis")

skills_list = clean_skills(df["skills"])
if skills_list:
    skill_df = skill_frequency(skills_list, top_n=15)
    fig_skills = plot_skill_frequency(skill_df)
    st.pyplot(fig_skills)

    with st.expander("📋 Full skill frequency table"):
        st.dataframe(
            skill_df.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No skill data available for the current selection.")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 2  SALARY DISTRIBUTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

st.header("💰 Salary Distribution")

tab_hist, tab_box = st.tabs(["Distribution Histogram", "By Job Role"])

with tab_hist:
    fig_salary = plot_salary_distribution(df)
    st.pyplot(fig_salary)

    # Summary stats row
    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        st.metric(
            "Salary Range (Low)",
            f"৳{metrics['min']:,.0f}" if metrics["min"] else "N/A",
        )
    with scol2:
        st.metric(
            "Salary Range (High)",
            f"৳{metrics['max']:,.0f}" if metrics["max"] else "N/A",
        )
    with scol3:
        st.metric("Postings with Salary", metrics["count"])

with tab_box:
    fig_box = plot_salary_by_role(df)
    if fig_box:
        st.pyplot(fig_box)
    else:
        st.info("Insufficient salary data for a role-level breakdown.")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 3  AI MARKET INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

st.header("🤖 AI Market Intelligence")
st.caption("Powered by Groq LLM — insights generated from your filtered data")

if st.button("Generate Market Summary", type="primary", use_container_width=True):
    with st.spinner("Analysing market data with AI …"):
        top_sk = top_skills_list(df, n=10)
        top_role = most_common_value(df["job_title"])
        top_ind = most_common_value(df["industry"])
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
    "**JobSeekAI** · Built with Streamlit · Data: Bangladesh Tech Job Market 2025"
)
