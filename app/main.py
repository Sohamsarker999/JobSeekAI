"""
main.py — JobSeekAI: Bangladesh Job Market Analytics Dashboard

Entry point for the Streamlit application.
Run with:  streamlit run app/main.py
"""

from __future__ import annotations

import sys
import os
from datetime import datetime

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

from ai_summary import generate_market_summary, generate_job_recommendations  # noqa: E402
from utils import (  # noqa: E402
    apply_filters,
    get_filter_options,
    load_data,
    most_common_value,
    top_skills_list,
    get_delta_jobs,
    get_jobs_today,
    get_new_companies_today,
    get_data_freshness,
    to_csv_bytes,
    to_pdf_bytes,
    get_degree_counts,
    get_experience_level_counts,
    get_industry_education_matrix,
)
from visualizations import (  # noqa: E402
    plot_industry_distribution,
    plot_top_companies,
    plot_location_distribution,
    plot_posting_trend,
    plot_experience_distribution,
    plot_degree_demand,
    plot_experience_levels,
    plot_industry_education_heatmap,
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background    : #f8fafc;
        border        : 1px solid #e2e8f0;
        border-radius : 10px;
        padding       : 16px 20px;
        transition    : box-shadow 0.2s;
    }
    [data-testid="stMetric"]:hover {
        box-shadow : 0 4px 12px rgba(37,99,235,0.10);
    }
    [data-testid="stMetricLabel"] {
        font-size      : 0.82rem;
        font-weight    : 600;
        color          : #64748b;
        text-transform : uppercase;
        letter-spacing : 0.04em;
    }
    [data-testid="stMetricValue"] {
        font-size   : 1.9rem;
        font-weight : 700;
        color       : #1e293b;
    }
    .hero-banner {
        background    : linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #0ea5e9 100%);
        border-radius : 14px;
        padding       : 36px 40px;
        margin-bottom : 28px;
        color         : white;
    }
    .hero-banner h1 {
        font-size   : 2.1rem;
        font-weight : 800;
        margin      : 0 0 8px 0;
        line-height : 1.2;
    }
    .hero-banner p { font-size: 1.05rem; opacity: 0.88; margin: 0; }
    .freshness-badge {
        display       : inline-flex;
        align-items   : center;
        gap           : 6px;
        padding       : 5px 14px;
        border-radius : 99px;
        font-size     : 0.82rem;
        font-weight   : 600;
        margin-top    : 14px;
    }
    .badge-fresh   { background:#dcfce7; color:#15803d; border:1px solid #86efac; }
    .badge-stale   { background:#fef9c3; color:#a16207; border:1px solid #fde047; }
    .badge-old     { background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; }
    .badge-unknown { background:#f1f5f9; color:#64748b; border:1px solid #cbd5e1; }
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
        "Industry", options=options["industry"], default=[],
        help="Leave empty to include all industries.",
    )
    sel_roles = st.multiselect(
        "Job Role", options=options["job_title"], default=[],
        help="Leave empty to include all roles.",
    )
    sel_locations = st.multiselect(
        "Location", options=options["location"], default=[],
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
# HERO BANNER
# ═══════════════════════════════════════════════════════════════════════════

freshness   = get_data_freshness(raw_df)
badge_class = f"badge-{freshness['status']}"
badge_text  = f"{freshness['emoji']} Data last updated: {freshness['last_updated']}"

st.markdown(
    f"""
    <div class="hero-banner">
        <h1>📊 JobSeekAI — Bangladesh Job Market</h1>
        <p>Live analytics on job demand, hiring trends, and AI-powered
        market intelligence — scraped daily from BDJobs.com</p>
        <div class="freshness-badge {badge_class}">{badge_text}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.warning(
        "No postings match your current filter selection. "
        "Try broadening your criteria or resetting filters."
    )
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
# KEY METRICS
# ═══════════════════════════════════════════════════════════════════════════

delta_jobs    = get_delta_jobs(raw_df)
jobs_today    = get_jobs_today(raw_df)
new_cos_today = get_new_companies_today(raw_df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📋 Total Postings",  f"{len(df):,}",
              delta=f"+{jobs_today} today" if jobs_today > 0 else "No new jobs today",
              delta_color="normal" if jobs_today > 0 else "off")
with col2:
    st.metric("🏢 Unique Companies", f"{df['company'].nunique():,}",
              delta=f"+{new_cos_today} new today" if new_cos_today > 0 else None)
with col3:
    st.metric("🏭 Industries", f"{df['industry'].nunique()}")
with col4:
    st.metric("📍 Locations",  f"{df['location'].nunique()}")

if delta_jobs > 0:
    st.success(f"📈 **{delta_jobs} more jobs posted today** compared to yesterday.")
elif delta_jobs < 0:
    st.info(f"📉 **{abs(delta_jobs)} fewer jobs posted today** compared to yesterday.")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 1  INDUSTRY & LOCATION OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

st.header("🏢 Market Overview")
col_left, col_right = st.columns(2)
with col_left:
    st.pyplot(plot_industry_distribution(df))
with col_right:
    st.pyplot(plot_location_distribution(df))

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 2  TOP HIRING COMPANIES
# ═══════════════════════════════════════════════════════════════════════════

st.header("🏆 Top Hiring Companies")
st.pyplot(plot_top_companies(df, top_n=12))
st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 3  POSTING TREND
# ═══════════════════════════════════════════════════════════════════════════

st.header("📈 Posting Trend")
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
    df[display_cols].rename(columns={
        "job_title":    "Job Title",
        "company":      "Company",
        "industry":     "Industry",
        "location":     "Location",
        "date_scraped": "Posted",
    }),
    use_container_width=True,
    hide_index=True,
    height=400,
)
st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 5  EDUCATION & EXPERIENCE ANALYTICS  ◄─ NEW FEATURE
# ═══════════════════════════════════════════════════════════════════════════

st.header("🎓 Education & Experience Analytics")
st.markdown(
    "Deep-dive into what qualifications and experience levels the "
    "Bangladesh job market is demanding right now."
)

tab_deg, tab_exp, tab_heat = st.tabs([
    "📜 Degree Demand",
    "💼 Experience Levels",
    "🔥 Industry × Education Heatmap",
])

# ── Tab 1: Degree Demand ───────────────────────────────────────────────────
with tab_deg:
    degree_counts = get_degree_counts(df)

    if degree_counts.empty:
        st.info(
            "No degree data found in your current dataset. "
            "This chart populates once the scraper collects education keywords "
            "such as BSc, MBA, Diploma etc. in the skills/education field."
        )
    else:
        fig_deg = plot_degree_demand(degree_counts)
        if fig_deg:
            st.pyplot(fig_deg)

        # Summary insight below the chart
        top_deg = degree_counts.iloc[0]
        st.success(
            f"🏆 **Most demanded qualification:** {top_deg['Degree']} "
            f"— required in **{top_deg['Count']}** postings "
            f"({top_deg['Count']/len(df)*100:.1f}% of filtered jobs)"
        )

        with st.expander("📊 View full degree breakdown table"):
            st.dataframe(
                degree_counts,
                use_container_width=True,
                hide_index=True,
            )

# ── Tab 2: Experience Levels ───────────────────────────────────────────────
with tab_exp:
    exp_counts = get_experience_level_counts(df)

    if exp_counts.empty or exp_counts["Count"].sum() == 0:
        st.info(
            "No experience-level data found yet. "
            "This chart appears once the scraper collects postings "
            "mentioning year requirements like '2 years', '5+ years' etc."
        )
    else:
        fig_exp_lvl = plot_experience_levels(exp_counts)
        if fig_exp_lvl:
            st.pyplot(fig_exp_lvl)

        # Insight callouts
        total_with_exp = exp_counts["Count"].sum()
        for _, row in exp_counts.iterrows():
            pct = row["Count"] / total_with_exp * 100
            if row["Level"].startswith("Entry"):
                icon = "🟢"
            elif row["Level"].startswith("Mid"):
                icon = "🔵"
            else:
                icon = "🟣"
            st.caption(f"{icon} **{row['Level']}** — {row['Count']} jobs ({pct:.1f}%)")

        with st.expander("📊 View experience level table"):
            st.dataframe(exp_counts, use_container_width=True, hide_index=True)

# ── Tab 3: Industry × Education Heatmap ───────────────────────────────────
with tab_heat:
    matrix = get_industry_education_matrix(df)

    if matrix.empty:
        st.info(
            "Not enough data to build the cross-analysis heatmap yet. "
            "This appears once there are jobs with both industry tags "
            "and recognised degree keywords."
        )
    else:
        st.markdown(
            "Each cell shows how many job postings in that industry "
            "require a given education level. **Darker = more demand.**"
        )
        fig_heat = plot_industry_education_heatmap(matrix)
        if fig_heat:
            st.pyplot(fig_heat)

        with st.expander("📊 View raw heatmap data"):
            st.dataframe(matrix, use_container_width=True)

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 6  AI MARKET INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

st.header("🤖 AI Market Intelligence")
st.caption("Powered by Groq LLM — insights generated from your filtered data")

if st.button("Generate Market Summary", type="primary", use_container_width=True):
    with st.spinner("Analysing market data with AI …"):
        top_sk   = top_skills_list(df, n=10)
        top_role = most_common_value(df["job_title"])
        top_ind  = most_common_value(df["industry"])
        metrics  = {"mean": None, "median": None, "min": None, "max": None, "count": 0}
        summary  = generate_market_summary(top_sk, metrics, top_role, top_ind)
    st.markdown(summary)
else:
    st.info(
        "Click **Generate Market Summary** to get an AI-powered executive "
        "brief based on the currently filtered data."
    )

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 7  AI-POWERED JOB RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

st.header("🎯 AI-Powered Job Recommendations")
st.markdown(
    "Describe your **skills, experience, and background** below. "
    "Our AI will scan today's job listings and surface your top matches — "
    "complete with a match score and explanation."
)

with st.form("rec_form"):
    user_profile = st.text_area(
        label="Your Skills & Experience",
        placeholder=(
            "Example:\n"
            "I have 2 years of experience in Python and data analysis. "
            "I know Pandas, SQL, and Power BI. I hold a BSc in CSE "
            "and am looking for a data or software role in Dhaka."
        ),
        height=160,
    )
    col_a, col_b = st.columns([3, 1])
    with col_b:
        top_n = st.selectbox("Show top", [3, 5, 7], index=1)

    submitted = st.form_submit_button(
        "🔍 Find My Best Matches", type="primary", use_container_width=True
    )

if submitted:
    if not user_profile.strip():
        st.warning("⚠️ Please enter your skills and experience before searching.")
    else:
        with st.spinner("AI is scanning job listings for you … (may take ~15 seconds)"):
            recommendations = generate_job_recommendations(user_profile, df, top_n=top_n)

        if not recommendations:
            st.error("No recommendations returned. Please try again.")
        elif "error" in recommendations[0]:
            st.error(recommendations[0]["error"])
        else:
            st.success(f"✅ Found your top **{len(recommendations)}** job matches!")
            st.markdown("---")

            for rec in recommendations:
                score = rec["match_score"]
                if score >= 80:
                    score_emoji, score_label = "🟢", "Strong Match"
                elif score >= 60:
                    score_emoji, score_label = "🟡", "Good Match"
                else:
                    score_emoji, score_label = "🔴", "Partial Match"

                with st.expander(
                    f"{score_emoji}  #{rec['rank']}  —  **{rec['job_title']}** "
                    f"@ {rec['company']}  |  Score: {score}/100  ({score_label})",
                    expanded=(rec["rank"] == 1),
                ):
                    m1, m2, m3 = st.columns(3)
                    m1.metric("📍 Location", rec["location"])
                    m2.metric("🏭 Industry",  rec["industry"])
                    m3.metric("🎯 Match",     f"{score}/100")
                    st.markdown(f"**🤖 Why this fits you:**  {rec['reason']}")
                    if rec.get("experience") and rec["experience"] not in ("N/A", "nan", ""):
                        st.caption(f"📋 Skills/Info: {rec['experience']}")
                    if rec.get("deadline") and rec["deadline"] not in ("N/A", "nan", ""):
                        st.caption(f"⏰ Deadline: {rec['deadline']}")

            st.markdown("---")
            st.caption(
                "💡 **Tip:** Apply filters in the sidebar (industry, location) "
                "before searching to narrow results to your preferred area."
            )

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# § 8  EXPORT & DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════

st.header("📥 Export & Download")
st.markdown(
    "Download the **currently filtered** job data as a CSV spreadsheet, "
    "or generate a formatted **PDF market report** with KPIs, rankings, and job listings."
)

active_filters = {
    "industries": sel_industries,
    "roles":      sel_roles,
    "locations":  sel_locations,
}
today_str = datetime.now().strftime("%Y-%m-%d")

col_csv, col_pdf = st.columns(2)

with col_csv:
    st.markdown("#### 📊 CSV Spreadsheet")
    st.markdown(
        f"Export all **{len(df):,} filtered job listings** to a spreadsheet. "
        "Open in Excel, Google Sheets, or any data tool."
    )
    st.download_button(
        label               = "⬇️ Download CSV",
        data                = to_csv_bytes(df),
        file_name           = f"jobseekAI_jobs_{today_str}.csv",
        mime                = "text/csv",
        use_container_width = True,
    )
    st.caption(f"File will contain {len(df):,} rows · UTF-8 encoded")

with col_pdf:
    st.markdown("#### 📄 PDF Market Report")
    st.markdown(
        "Generate a formatted report with key metrics, top companies, "
        "industries, locations, and job listings."
    )
    if st.button("⬇️ Generate & Download PDF", use_container_width=True, key="pdf_btn"):
        with st.spinner("Building your PDF report …"):
            try:
                pdf_bytes = to_pdf_bytes(df, active_filters)
                st.download_button(
                    label               = "📄 Click here to save your PDF",
                    data                = pdf_bytes,
                    file_name           = f"jobseekAI_report_{today_str}.pdf",
                    mime                = "application/pdf",
                    use_container_width = True,
                    type                = "primary",
                )
                st.success("✅ PDF ready! Click the button above to download.")
            except Exception as e:
                st.error(
                    f"⚠️ Could not generate PDF: {e}\n\n"
                    "Make sure `reportlab` is in your `requirements.txt`."
                )
    st.caption("Includes KPIs · Top 10 rankings · First 30 job listings")


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption(
    "**JobSeekAI** · Built with Streamlit · Live data from BDJobs.com · "
    "Auto-updated daily"
)
