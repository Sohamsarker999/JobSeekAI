"""
utils.py — Data loading, cleaning, and metric computation for JobSeekAI.

Reads from Google Sheets (live data) with fallback to local CSV.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Google Sheets Configuration
# ---------------------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

SHEET_NAME = "BDJobs Data"
CSV_FALLBACK = os.path.join(os.path.dirname(__file__), "data", "job_postings.csv")


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------


def _get_google_creds():
    """Get Google credentials from Streamlit secrets or environment."""
    try:
        creds_data = st.secrets["GOOGLE_CREDENTIALS"]
        if isinstance(creds_data, str):
            creds_data = json.loads(creds_data)
        else:
            creds_data = dict(creds_data)
        return Credentials.from_service_account_info(creds_data, scopes=SCOPES)
    except Exception:
        pass

    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        return Credentials.from_service_account_info(
            json.loads(creds_json), scopes=SCOPES
        )
    return None


@st.cache_data(ttl=3600, show_spinner="Loading live job data …")
def load_data() -> pd.DataFrame:
    """Load data from Google Sheets. Falls back to local CSV if unavailable."""
    creds = _get_google_creds()

    if creds:
        try:
            client = gspread.authorize(creds)
            spreadsheet = client.open(SHEET_NAME)
            worksheet = spreadsheet.sheet1
            data = worksheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                df = _clean_dataframe(df)
                return df
        except Exception as e:
            st.warning(f"Could not load Google Sheet. Using local CSV. ({e})")

    if os.path.exists(CSV_FALLBACK):
        df = pd.read_csv(CSV_FALLBACK)
        df = _clean_dataframe(df)
        return df

    return pd.DataFrame(
        columns=[
            "job_title", "company", "salary_min", "salary_max",
            "skills", "industry", "location",
        ]
    )


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise columns and fix types."""
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    for col in ("salary_min", "salary_max"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    mask = (
        df["salary_min"].notna()
        & df["salary_max"].notna()
        & (df["salary_min"] > df["salary_max"])
    )
    if mask.any():
        df.loc[mask, ["salary_min", "salary_max"]] = (
            df.loc[mask, ["salary_max", "salary_min"]].values
        )

    text_cols = ["job_title", "company", "skills", "industry", "location"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df = df[~df["job_title"].isin(["", "nan"])].reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Skill Processing
# ---------------------------------------------------------------------------


def clean_skills(series: pd.Series) -> List[str]:
    """Parse comma-separated skill strings into a flat, normalised list."""
    all_skills: List[str] = []
    for entry in series.dropna():
        entry_str = str(entry).strip()
        if entry_str.lower() in ("", "nan"):
            continue
        skills = [s.strip().lower() for s in entry_str.split(",") if s.strip()]
        all_skills.extend(skills)
    return all_skills


def skill_frequency(skills: List[str], top_n: int = 15) -> pd.DataFrame:
    """Return a DataFrame of the top_n most frequent skills."""
    counter = Counter(skills)
    most_common = counter.most_common(top_n)
    df = pd.DataFrame(most_common, columns=["Skill", "Frequency"])
    return df.sort_values("Frequency", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Salary Metrics
# ---------------------------------------------------------------------------


def calculate_salary_metrics(df: pd.DataFrame) -> Dict[str, float | None]:
    """Compute mean, median, min, max of average salary."""
    valid = df.dropna(subset=["salary_min", "salary_max"])
    if valid.empty:
        return {"mean": None, "median": None, "min": None, "max": None, "count": 0}

    avg = (valid["salary_min"] + valid["salary_max"]) / 2
    return {
        "mean":   round(avg.mean(),   0),
        "median": round(avg.median(), 0),
        "min":    round(avg.min(),    0),
        "max":    round(avg.max(),    0),
        "count":  len(avg),
    }


def add_avg_salary_column(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with an avg_salary column appended."""
    out = df.copy()
    out["avg_salary"] = (out["salary_min"] + out["salary_max"]) / 2
    return out


# ---------------------------------------------------------------------------
# Filtering Helpers
# ---------------------------------------------------------------------------


def get_filter_options(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Extract unique sorted values for each filterable column."""
    return {
        "industry":  sorted(df["industry"].dropna().unique().tolist()),
        "job_title": sorted(df["job_title"].dropna().unique().tolist()),
        "location":  sorted(df["location"].dropna().unique().tolist()),
    }


def apply_filters(
    df: pd.DataFrame,
    industries: List[str],
    job_titles: List[str],
    locations: List[str],
) -> pd.DataFrame:
    """Return the subset of df that matches all selected filter values."""
    filtered = df.copy()
    if industries:
        filtered = filtered[filtered["industry"].isin(industries)]
    if job_titles:
        filtered = filtered[filtered["job_title"].isin(job_titles)]
    if locations:
        filtered = filtered[filtered["location"].isin(locations)]
    return filtered


# ---------------------------------------------------------------------------
# Summary Helpers
# ---------------------------------------------------------------------------


def top_skills_list(df: pd.DataFrame, n: int = 10) -> List[Tuple[str, int]]:
    """Return the top n (skill, count) pairs."""
    skills = clean_skills(df["skills"])
    return Counter(skills).most_common(n)


def most_common_value(series: pd.Series) -> str:
    """Return the most frequent non-null value in series, or 'N/A'."""
    mode = series.mode()
    return mode.iloc[0] if not mode.empty else "N/A"


# ---------------------------------------------------------------------------
# NEW: KPI Delta Helpers
# ---------------------------------------------------------------------------


def get_jobs_today(df: pd.DataFrame) -> int:
    """Count jobs scraped today (based on date_scraped column)."""
    if "date_scraped" not in df.columns:
        return 0
    today = pd.Timestamp.now().normalize()
    dates = pd.to_datetime(df["date_scraped"], errors="coerce")
    return int((dates >= today).sum())


def get_jobs_yesterday(df: pd.DataFrame) -> int:
    """Count jobs scraped yesterday."""
    if "date_scraped" not in df.columns:
        return 0
    today     = pd.Timestamp.now().normalize()
    yesterday = today - pd.Timedelta(days=1)
    dates     = pd.to_datetime(df["date_scraped"], errors="coerce")
    return int(((dates >= yesterday) & (dates < today)).sum())


def get_delta_jobs(df: pd.DataFrame) -> int:
    """Return today's job count minus yesterday's (can be negative)."""
    return get_jobs_today(df) - get_jobs_yesterday(df)


def get_new_companies_today(df: pd.DataFrame) -> int:
    """Count companies that posted a job for the first time today."""
    if "date_scraped" not in df.columns:
        return 0

    dates = pd.to_datetime(df["date_scraped"], errors="coerce")
    today = pd.Timestamp.now().normalize()

    today_companies = set(df.loc[dates >= today, "company"].dropna().unique())
    prev_companies  = set(df.loc[dates < today,  "company"].dropna().unique())

    # Companies that appear today but never before
    return len(today_companies - prev_companies)


def get_data_freshness(df: pd.DataFrame) -> dict:
    """
    Return a dict describing how fresh the data is.

    Keys:
        last_updated : str  — human-readable timestamp or "Unknown"
        hours_ago    : float | None
        status       : "fresh" | "stale" | "old" | "unknown"
        color        : green / orange / red / gray (for badge styling)
        emoji        : matching emoji
    """
    if "date_scraped" not in df.columns or df.empty:
        return {
            "last_updated": "Unknown",
            "hours_ago":    None,
            "status":       "unknown",
            "color":        "gray",
            "emoji":        "⚪",
        }

    dates      = pd.to_datetime(df["date_scraped"], errors="coerce").dropna()
    if dates.empty:
        return {
            "last_updated": "Unknown",
            "hours_ago":    None,
            "status":       "unknown",
            "color":        "gray",
            "emoji":        "⚪",
        }

    latest     = dates.max()
    now        = pd.Timestamp.now()
    hours_ago  = (now - latest).total_seconds() / 3600

    # Format nicely
    if hours_ago < 1:
        mins = int(hours_ago * 60)
        label = f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif hours_ago < 24:
        hrs = int(hours_ago)
        label = f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    else:
        days = int(hours_ago // 24)
        label = f"{days} day{'s' if days != 1 else ''} ago"

    if hours_ago <= 6:
        status, color, emoji = "fresh",   "#16a34a", "🟢"
    elif hours_ago <= 24:
        status, color, emoji = "stale",   "#d97706", "🟡"
    else:
        status, color, emoji = "old",     "#dc2626", "🔴"

    return {
        "last_updated": label,
        "hours_ago":    round(hours_ago, 1),
        "status":       status,
        "color":        color,
        "emoji":        emoji,
    }
