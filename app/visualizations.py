"""
visualizations.py — Chart rendering for JobSeekAI.

Focused on: industry distribution, location, top companies,
job posting trends, and experience/education breakdown.
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
    "primary": "#2563EB",
    "secondary": "#10B981",
    "accent": "#F59E0B",
    "dark": "#1E293B",
    "muted": "#94A3B8",
}

PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
           "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16"]


# ---------------------------------------------------------------------------
# Industry Distribution (Pie / Donut)
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
    data = counts.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))

    bars = ax.barh(
        data.index,
        data.values,
        color=COLORS["primary"],
        edgecolor="white",
        height=0.65,
    )

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.2,
            bar.get_y() + bar.get_height() / 2,
            str(int(width)),
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#333333",
        )

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
    # Clean and split multi-location entries, take first location
    locations = df["location"].apply(
        lambda x: str(x).split(",")[0].strip() if pd.notna(x) else "Dhaka"
    )
    counts = locations.value_counts().head(top_n)
    data = counts.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))

    bars = ax.barh(
        data.index,
        data.values,
        color=COLORS["secondary"],
        edgecolor="white",
        height=0.65,
    )

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.2,
            bar.get_y() + bar.get_height() / 2,
            str(int(width)),
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#333333",
        )

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

    daily = df_copy.groupby("date_scraped").size().reset_index(name="count")
    daily = daily.sort_values("date_scraped")

    if len(daily) < 2:
        return None

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.fill_between(daily["date_scraped"], daily["count"], alpha=0.15, color=COLORS["primary"])
    ax.plot(
        daily["date_scraped"],
        daily["count"],
        color=COLORS["primary"],
        linewidth=2.5,
        marker="o",
        markersize=6,
    )

    ax.set_xlabel("Date", fontsize=11, labelpad=10)
    ax.set_ylabel("New Postings", fontsize=11, labelpad=10)
    ax.set_title("Daily Job Posting Trend", fontsize=14, fontweight="bold", pad=14)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Experience Requirements
# ---------------------------------------------------------------------------


def plot_experience_distribution(df: pd.DataFrame) -> Optional[plt.Figure]:
    """Bar chart of experience requirements extracted from skills column."""
    if "skills" not in df.columns:
        return None

    # Extract experience info
    exp_data = df["skills"].dropna().astype(str)
    exp_data = exp_data[exp_data.str.contains("Experience:", case=False)]
    exp_data = exp_data.str.extract(r"Experience:\s*(.+?)(?:,|$)", expand=False)
    exp_data = exp_data.dropna().str.strip()

    if exp_data.empty:
        return None

    counts = exp_data.value_counts().head(8)
    data = counts.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.45)))

    bars = ax.barh(
        data.index,
        data.values,
        color=COLORS["accent"],
        edgecolor="white",
        height=0.65,
    )

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.2,
            bar.get_y() + bar.get_height() / 2,
            str(int(width)),
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#333333",
        )

    ax.set_xlabel("Number of Postings", fontsize=11, labelpad=10)
    ax.set_title("Experience Requirements", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    return fig
