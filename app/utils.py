"""
utils.py — Data loading, cleaning, and metric computation for JobSeekAI.

Handles:
  • CSV ingestion with defensive parsing
  • Skill normalization and frequency counting
  • Salary metric calculations
  • Filter application logic
"""

from __future__ import annotations

import os
from collections import Counter
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "job_postings.csv")


@st.cache_data(show_spinner="Loading job postings …")
def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    """Read the CSV and apply initial type coercion / validation.

    Returns a cleaned DataFrame ready for downstream analysis.
    """
    df = pd.read_csv(path)

    # Standardise column names (strip whitespace, lowercase)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Coerce salary columns to numeric (invalid → NaN)
    for col in ("salary_min", "salary_max"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Auto-correct rows where salary_min > salary_max by swapping
    mask = df["salary_min"] > df["salary_max"]
    df.loc[mask, ["salary_min", "salary_max"]] = (
        df.loc[mask, ["salary_max", "salary_min"]].values
    )

    # Strip whitespace from text columns
    text_cols = ["job_title", "company", "skills", "industry", "location"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


# ---------------------------------------------------------------------------
# Skill Processing
# ---------------------------------------------------------------------------


def clean_skills(series: pd.Series) -> List[str]:
    """Parse comma-separated skill strings into a flat, normalised list.

    Steps:
      1. Drop NaN / 'nan' values
      2. Split on commas
      3. Strip whitespace, convert to lowercase
      4. Remove empty strings
    """
    all_skills: List[str] = []
    for entry in series.dropna():
        entry_str = str(entry).strip()
        if entry_str.lower() in ("", "nan"):
            continue
        skills = [s.strip().lower() for s in entry_str.split(",") if s.strip()]
        all_skills.extend(skills)
    return all_skills


def skill_frequency(skills: List[str], top_n: int = 15) -> pd.DataFrame:
    """Return a DataFrame of the *top_n* most frequent skills, sorted descending."""
    counter = Counter(skills)
    most_common = counter.most_common(top_n)
    df = pd.DataFrame(most_common, columns=["Skill", "Frequency"])
    return df.sort_values("Frequency", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Salary Metrics
# ---------------------------------------------------------------------------


def calculate_salary_metrics(df: pd.DataFrame) -> Dict[str, float | None]:
    """Compute mean, median, min, and max of the average salary.

    avg_salary = (salary_min + salary_max) / 2
    Rows with missing salary data are excluded.
    """
    valid = df.dropna(subset=["salary_min", "salary_max"])
    if valid.empty:
        return {"mean": None, "median": None, "min": None, "max": None, "count": 0}

    avg = (valid["salary_min"] + valid["salary_max"]) / 2
    return {
        "mean": round(avg.mean(), 0),
        "median": round(avg.median(), 0),
        "min": round(avg.min(), 0),
        "max": round(avg.max(), 0),
        "count": len(avg),
    }


def add_avg_salary_column(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with an ``avg_salary`` column appended."""
    out = df.copy()
    out["avg_salary"] = (out["salary_min"] + out["salary_max"]) / 2
    return out


# ---------------------------------------------------------------------------
# Filtering Helpers
# ---------------------------------------------------------------------------


def get_filter_options(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Extract unique sorted values for each filterable column."""
    return {
        "industry": sorted(df["industry"].dropna().unique().tolist()),
        "job_title": sorted(df["job_title"].dropna().unique().tolist()),
        "location": sorted(df["location"].dropna().unique().tolist()),
    }


def apply_filters(
    df: pd.DataFrame,
    industries: List[str],
    job_titles: List[str],
    locations: List[str],
) -> pd.DataFrame:
    """Return the subset of *df* that matches **all** selected filter values.

    An empty selection for a dimension means "include all".
    """
    filtered = df.copy()
    if industries:
        filtered = filtered[filtered["industry"].isin(industries)]
    if job_titles:
        filtered = filtered[filtered["job_title"].isin(job_titles)]
    if locations:
        filtered = filtered[filtered["location"].isin(locations)]
    return filtered


# ---------------------------------------------------------------------------
# Summary Helpers (used by AI module)
# ---------------------------------------------------------------------------


def top_skills_list(df: pd.DataFrame, n: int = 10) -> List[Tuple[str, int]]:
    """Return the top *n* (skill, count) pairs from the current DataFrame."""
    skills = clean_skills(df["skills"])
    return Counter(skills).most_common(n)


def most_common_value(series: pd.Series) -> str:
    """Return the most frequent non-null value in *series*, or 'N/A'."""
    mode = series.mode()
    return mode.iloc[0] if not mode.empty else "N/A"
