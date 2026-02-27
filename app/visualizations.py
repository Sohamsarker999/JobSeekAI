"""
visualizations.py — Chart rendering for JobSeekAI.

All public functions return a ``matplotlib.figure.Figure`` so the caller
can pass it straight to ``st.pyplot()``.
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Global style configuration
# ---------------------------------------------------------------------------

sns.set_theme(style="whitegrid", font_scale=0.95)
PALETTE_MAIN = "#2563EB"       # primary blue
PALETTE_ACCENT = "#10B981"     # accent green
PALETTE_MULTI = "coolwarm"

BDT_FORMATTER = mticker.FuncFormatter(lambda x, _: f"৳{x:,.0f}")


# ---------------------------------------------------------------------------
# Skill Frequency Bar Chart
# ---------------------------------------------------------------------------


def plot_skill_frequency(skill_df: pd.DataFrame) -> plt.Figure:
    """Horizontal bar chart of the top skills sorted by frequency.

    Parameters
    ----------
    skill_df : DataFrame with columns ``["Skill", "Frequency"]``.
    """
    fig, ax = plt.subplots(figsize=(10, max(5, len(skill_df) * 0.45)))

    # Plot in ascending order so highest frequency appears at top
    data = skill_df.sort_values("Frequency", ascending=True)

    bars = ax.barh(
        data["Skill"],
        data["Frequency"],
        color=PALETTE_MAIN,
        edgecolor="white",
        height=0.65,
    )

    # Value labels on each bar
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(int(width)),
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#333333",
        )

    ax.set_xlabel("Frequency", fontsize=11, labelpad=10)
    ax.set_title("Top Skills in Demand", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Salary Distribution Histogram
# ---------------------------------------------------------------------------


def plot_salary_distribution(df: pd.DataFrame) -> plt.Figure:
    """Histogram of average salary values with a KDE overlay.

    Expects the DataFrame to already contain an ``avg_salary`` column.
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    sns.histplot(
        df["avg_salary"].dropna(),
        bins=20,
        kde=True,
        color=PALETTE_MAIN,
        edgecolor="white",
        ax=ax,
    )

    ax.set_xlabel("Average Salary (BDT)", fontsize=11, labelpad=10)
    ax.set_ylabel("Number of Postings", fontsize=11, labelpad=10)
    ax.set_title(
        "Salary Distribution Across Postings",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )
    ax.xaxis.set_major_formatter(BDT_FORMATTER)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Salary Boxplot by Job Title
# ---------------------------------------------------------------------------


def plot_salary_by_role(
    df: pd.DataFrame, max_roles: int = 12
) -> Optional[plt.Figure]:
    """Box plot of average salary grouped by job title.

    Only the *max_roles* most common titles are shown to avoid clutter.
    Returns ``None`` if insufficient data.
    """
    valid = df.dropna(subset=["avg_salary"])
    if valid.empty:
        return None

    # Keep only the N most frequent roles
    top_roles = valid["job_title"].value_counts().head(max_roles).index
    subset = valid[valid["job_title"].isin(top_roles)]

    # Order roles by median salary descending
    order = (
        subset.groupby("job_title")["avg_salary"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    fig, ax = plt.subplots(figsize=(10, max(5, len(order) * 0.5)))

    sns.boxplot(
        data=subset,
        y="job_title",
        x="avg_salary",
        order=order,
        palette="Blues_r",
        linewidth=1.2,
        ax=ax,
    )

    ax.set_xlabel("Average Salary (BDT)", fontsize=11, labelpad=10)
    ax.set_ylabel("")
    ax.set_title(
        "Salary Range by Job Role",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )
    ax.xaxis.set_major_formatter(BDT_FORMATTER)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    return fig
