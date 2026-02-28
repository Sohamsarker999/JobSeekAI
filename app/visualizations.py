"""
visualizations.py — Chart rendering for JobSeekAI.

Covers: industry distribution, location, top companies,
job posting trends, experience/education breakdown,
degree demand, experience level distribution, industry-education heatmap.
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------

sns.set_theme(style="whitegrid", font_scale=0.95)

COLORS = {
    "primary":   "#2563EB",
    "secondary": "#10B981",
    "accent":    "#F59E0B",
    "dark":      "#1E293B",
    "muted":     "#94A3B8",
    "purple":    "#8B5CF6",
}

PALETTE = [
    "#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
    "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
]

# Ordered level colours for experience buckets
EXP_COLORS = ["#10B981", "#2563EB", "#8B5CF6"]   # Entry, Mid, Senior


# ---------------------------------------------------------------------------
# Industry Distribution (Donut)
# ---------------------------------------------------------------------------


def plot_industry_distribution(df: pd.DataFrame) -> plt.Figure:
    """Donut chart showing job distribution across industries."""
    counts = df["industry"].value_counts().head(8)

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.0f%%",
        colors=PALETTE[: len(counts)],
        startangle=90,
        pctdistance=0.78,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(9)

    ax.set_title("Jobs by Industry", fontsize=14, fontweight="bold", pad=16)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Top Companies Bar Chart
# ---------------------------------------------------------------------------


def plot_top_companies(df: pd.DataFrame, top_n: int = 12) -> plt.Figure:
    """Horizontal bar chart of companies with most job postings."""
    counts = df["company"].value_counts().head(top_n)
    data   = counts.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))
    bars = ax.barh(data.index, data.values,
                   color=COLORS["primary"], edgecolor="white", height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.2, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va="center", fontsize=9,
                fontweight="bold", color="#333333")

    ax.set_xlabel("Number of Openings", fontsize=11, labelpad=10)
    ax.set_title("Top Hiring Companies", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Location Distribution
# ---------------------------------------------------------------------------


def plot_location_distribution(df: pd.DataFrame, top_n: int = 10) -> plt.Figure:
    """Bar chart of job postings by location."""
    locations = df["location"].apply(
        lambda x: str(x).split(",")[0].strip() if pd.notna(x) else "Dhaka"
    )
    counts = locations.value_counts().head(top_n)
    data   = counts.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))
    bars = ax.barh(data.index, data.values,
                   color=COLORS["secondary"], edgecolor="white", height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.2, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va="center", fontsize=9,
                fontweight="bold", color="#333333")

    ax.set_xlabel("Number of Postings", fontsize=11, labelpad=10)
    ax.set_title("Jobs by Location", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Posting Trend Over Time
# ---------------------------------------------------------------------------


def plot_posting_trend(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Line chart showing job postings over time."""
    if "date_scraped" not in df.columns:
        return None

    df_copy = df.copy()
    df_copy["date_scraped"] = pd.to_datetime(df_copy["date_scraped"], errors="coerce")
    df_copy = df_copy.dropna(subset=["date_scraped"])

    if df_copy.empty:
        return None

    daily = (
        df_copy.groupby("date_scraped")
        .size()
        .reset_index(name="count")
        .sort_values("date_scraped")
    )

    if len(daily) < 2:
        return None

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(daily["date_scraped"], daily["count"],
                    alpha=0.15, color=COLORS["primary"])
    ax.plot(daily["date_scraped"], daily["count"],
            color=COLORS["primary"], linewidth=2.5, marker="o", markersize=6)

    ax.set_xlabel("Date", fontsize=11, labelpad=10)
    ax.set_ylabel("New Postings", fontsize=11, labelpad=10)
    ax.set_title("Daily Job Posting Trend", fontsize=14, fontweight="bold", pad=14)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Experience Requirements (raw from skills column)
# ---------------------------------------------------------------------------


def plot_experience_distribution(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Bar chart of experience requirements extracted from skills column."""
    if "skills" not in df.columns:
        return None

    exp_data = df["skills"].dropna().astype(str)
    exp_data = exp_data[exp_data.str.contains("Experience:", case=False)]
    exp_data = exp_data.str.extract(r"Experience:\s*(.+?)(?:,|$)", expand=False)
    exp_data = exp_data.dropna().str.strip()

    if exp_data.empty:
        return None

    counts = exp_data.value_counts().head(8)
    data   = counts.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.45)))
    bars = ax.barh(data.index, data.values,
                   color=COLORS["accent"], edgecolor="white", height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.2, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va="center", fontsize=9,
                fontweight="bold", color="#333333")

    ax.set_xlabel("Number of Postings", fontsize=11, labelpad=10)
    ax.set_title("Experience Requirements", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# NEW: Most Demanded Degrees
# ---------------------------------------------------------------------------


def plot_degree_demand(degree_counts: pd.DataFrame) -> Optional[plt.Figure]:
    """
    Horizontal bar chart of most demanded degrees.

    Parameters
    ----------
    degree_counts : pd.DataFrame
        Output of utils.get_degree_counts() — columns: Degree, Count
    """
    if degree_counts.empty:
        return None

    data = degree_counts.sort_values("Count", ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.5)))

    bars = ax.barh(
        data["Degree"], data["Count"],
        color=COLORS["purple"], edgecolor="white", height=0.6,
    )

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.2, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va="center", fontsize=9,
                fontweight="bold", color="#333333")

    ax.set_xlabel("Number of Job Postings", fontsize=11, labelpad=10)
    ax.set_title("Most In-Demand Degrees", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# NEW: Experience Level Distribution (Entry / Mid / Senior)
# ---------------------------------------------------------------------------


def plot_experience_levels(exp_counts: pd.DataFrame) -> Optional[plt.Figure]:
    """
    Coloured bar chart for Entry / Mid / Senior level distribution.

    Parameters
    ----------
    exp_counts : pd.DataFrame
        Output of utils.get_experience_level_counts() — columns: Level, Count
    """
    if exp_counts.empty or exp_counts["Count"].sum() == 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 4))

    colors_list = EXP_COLORS[: len(exp_counts)]
    bars = ax.bar(
        exp_counts["Level"], exp_counts["Count"],
        color=colors_list, edgecolor="white", width=0.5,
    )

    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + 0.5,
            str(int(h)), ha="center", va="bottom",
            fontsize=11, fontweight="bold", color="#333333",
        )

    total = exp_counts["Count"].sum()
    pcts  = [f"{v/total*100:.0f}%" for v in exp_counts["Count"]]
    ax.set_xticks(range(len(exp_counts)))
    ax.set_xticklabels(
        [f"{lvl}\n({pct})" for lvl, pct in zip(exp_counts["Level"], pcts)],
        fontsize=10,
    )

    ax.set_ylabel("Number of Postings", fontsize=11, labelpad=10)
    ax.set_title("Experience Level Distribution", fontsize=14, fontweight="bold", pad=14)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# NEW: Industry × Education Heatmap
# ---------------------------------------------------------------------------


def plot_industry_education_heatmap(matrix: pd.DataFrame) -> Optional[plt.Figure]:
    """
    Seaborn heatmap — rows: top industries, columns: degree types.
    Cell values = number of job postings requiring that degree in that industry.

    Parameters
    ----------
    matrix : pd.DataFrame
        Output of utils.get_industry_education_matrix()
    """
    if matrix.empty:
        return None

    fig, ax = plt.subplots(
        figsize=(max(8, len(matrix.columns) * 1.4),
                 max(5, len(matrix.index) * 0.7))
    )

    sns.heatmap(
        matrix,
        ax          = ax,
        annot       = True,
        fmt         = "d",
        cmap        = "Blues",
        linewidths  = 0.5,
        linecolor   = "#e2e8f0",
        cbar_kws    = {"label": "Job Postings", "shrink": 0.7},
        annot_kws   = {"size": 10, "weight": "bold"},
    )

    ax.set_title(
        "Industry × Education Requirements",
        fontsize=14, fontweight="bold", pad=16,
    )
    ax.set_xlabel("Degree / Education Level", fontsize=11, labelpad=10)
    ax.set_ylabel("Industry", fontsize=11, labelpad=10)
    ax.tick_params(axis="x", rotation=30, labelsize=9)
    ax.tick_params(axis="y", rotation=0,  labelsize=9)

    fig.tight_layout()
    return fig
