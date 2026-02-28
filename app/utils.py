"""
utils.py — Data loading, cleaning, and metric computation for JobSeekAI.

Reads from Google Sheets (live data) with fallback to local CSV.
"""

from __future__ import annotations

import io
import json
import os
from collections import Counter
from datetime import datetime
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
# KPI Delta Helpers
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
    return len(today_companies - prev_companies)


def get_data_freshness(df: pd.DataFrame) -> dict:
    """
    Return a dict describing how fresh the data is.
    Keys: last_updated, hours_ago, status, color, emoji
    """
    if "date_scraped" not in df.columns or df.empty:
        return {
            "last_updated": "Unknown",
            "hours_ago":    None,
            "status":       "unknown",
            "color":        "gray",
            "emoji":        "⚪",
        }

    dates = pd.to_datetime(df["date_scraped"], errors="coerce").dropna()
    if dates.empty:
        return {
            "last_updated": "Unknown",
            "hours_ago":    None,
            "status":       "unknown",
            "color":        "gray",
            "emoji":        "⚪",
        }

    latest    = dates.max()
    now       = pd.Timestamp.now()
    hours_ago = (now - latest).total_seconds() / 3600

    if hours_ago < 1:
        mins  = int(hours_ago * 60)
        label = f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif hours_ago < 24:
        hrs   = int(hours_ago)
        label = f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    else:
        days  = int(hours_ago // 24)
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


# ---------------------------------------------------------------------------
# NEW: Export Helpers
# ---------------------------------------------------------------------------


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Convert a DataFrame to UTF-8 encoded CSV bytes, ready for st.download_button.
    Renames columns to be human-friendly before export.
    """
    export_df = df.copy()

    # Rename columns to be human-readable in the exported file
    rename_map = {
        "job_title":    "Job Title",
        "company":      "Company",
        "industry":     "Industry",
        "location":     "Location",
        "skills":       "Skills / Requirements",
        "salary_min":   "Salary Min (BDT)",
        "salary_max":   "Salary Max (BDT)",
        "date_scraped": "Date Scraped",
        "deadline":     "Application Deadline",
    }
    export_df = export_df.rename(columns={k: v for k, v in rename_map.items() if k in export_df.columns})

    return export_df.to_csv(index=False).encode("utf-8")


def to_pdf_bytes(
    df: pd.DataFrame,
    active_filters: dict,
) -> bytes:
    """
    Generate a formatted PDF market report from the filtered DataFrame.
    Uses reportlab for layout. Returns raw PDF bytes.

    Parameters
    ----------
    df             : filtered DataFrame currently shown in the dashboard
    active_filters : dict with keys 'industries', 'roles', 'locations'
                     (each a list — empty means "All")
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize    = A4,
        leftMargin  = 2 * cm,
        rightMargin = 2 * cm,
        topMargin   = 2 * cm,
        bottomMargin= 2 * cm,
    )

    # ── Colour palette (matches dashboard) ────────────────────────────────
    BLUE   = colors.HexColor("#2563EB")
    DARK   = colors.HexColor("#1e293b")
    LIGHT  = colors.HexColor("#f8fafc")
    MUTED  = colors.HexColor("#64748b")
    GREEN  = colors.HexColor("#16a34a")
    WHITE  = colors.white

    # ── Styles ─────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent    = styles["Heading1"],
        fontSize  = 22,
        textColor = BLUE,
        spaceAfter= 4,
        fontName  = "Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent    = styles["Normal"],
        fontSize  = 10,
        textColor = MUTED,
        spaceAfter= 2,
        fontName  = "Helvetica",
    )
    section_style = ParagraphStyle(
        "Section",
        parent    = styles["Heading2"],
        fontSize  = 13,
        textColor = DARK,
        spaceBefore= 18,
        spaceAfter = 6,
        fontName  = "Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body",
        parent    = styles["Normal"],
        fontSize  = 9.5,
        textColor = DARK,
        leading   = 14,
        fontName  = "Helvetica",
    )
    small_style = ParagraphStyle(
        "Small",
        parent    = styles["Normal"],
        fontSize  = 8,
        textColor = MUTED,
        fontName  = "Helvetica",
    )

    # ── Helper: build a simple two-column table ────────────────────────────
    def kv_table(rows: list[tuple]) -> Table:
        """rows = [(label, value), ...]"""
        data = [[Paragraph(f"<b>{k}</b>", body_style),
                 Paragraph(str(v), body_style)] for k, v in rows]
        t = Table(data, colWidths=[5 * cm, 11 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT),
            ("TEXTCOLOR",  (0, 0), (0, -1), DARK),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT]),
            ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        return t

    def ranking_table(title_col: str, count_col: str, data_rows: list[tuple]) -> Table:
        """Ranked table with header row."""
        header = [
            Paragraph(f"<b>#</b>",         body_style),
            Paragraph(f"<b>{title_col}</b>", body_style),
            Paragraph(f"<b>{count_col}</b>", body_style),
        ]
        rows = [header] + [
            [Paragraph(str(i + 1), body_style),
             Paragraph(str(name),  body_style),
             Paragraph(str(count), body_style)]
            for i, (name, count) in enumerate(data_rows)
        ]
        t = Table(rows, colWidths=[1.2 * cm, 10.5 * cm, 4.3 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("ALIGN",        (2, 0), (2, -1), "CENTER"),
        ]))
        return t

    # ── Compute stats ──────────────────────────────────────────────────────
    total_jobs      = len(df)
    unique_companies= df["company"].nunique()
    unique_industries = df["industry"].nunique()
    unique_locations= df["location"].nunique()

    top_companies   = df["company"].value_counts().head(10)
    top_industries  = df["industry"].value_counts().head(10)
    top_locations   = df["location"].value_counts().head(10)
    top_roles       = df["job_title"].value_counts().head(10)

    generated_at    = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # Filter summary line
    f_ind = ", ".join(active_filters.get("industries", [])) or "All"
    f_rol = ", ".join(active_filters.get("roles",      [])) or "All"
    f_loc = ", ".join(active_filters.get("locations",  [])) or "All"

    # ── Build the PDF story ────────────────────────────────────────────────
    story = []

    # Title block
    story.append(Paragraph("📊 JobSeekAI", title_style))
    story.append(Paragraph("Bangladesh Job Market Report", subtitle_style))
    story.append(Paragraph(f"Generated: {generated_at}", small_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.4 * cm))

    # Active filters
    story.append(Paragraph("Active Filters", section_style))
    story.append(kv_table([
        ("Industry",  f_ind),
        ("Job Role",  f_rol),
        ("Location",  f_loc),
    ]))

    # KPI Summary
    story.append(Paragraph("Key Metrics", section_style))
    story.append(kv_table([
        ("Total Job Postings",  f"{total_jobs:,}"),
        ("Unique Companies",    f"{unique_companies:,}"),
        ("Industries Covered",  f"{unique_industries}"),
        ("Locations Covered",   f"{unique_locations}"),
    ]))

    # Top Companies
    story.append(Paragraph("Top 10 Hiring Companies", section_style))
    story.append(ranking_table(
        "Company", "Postings",
        [(name, count) for name, count in top_companies.items()]
    ))

    # Top Industries
    story.append(Paragraph("Top 10 Industries", section_style))
    story.append(ranking_table(
        "Industry", "Postings",
        [(name, count) for name, count in top_industries.items()]
    ))

    # Top Locations
    story.append(Paragraph("Top 10 Locations", section_style))
    story.append(ranking_table(
        "Location", "Postings",
        [(name, count) for name, count in top_locations.items()]
    ))

    # Top Job Roles
    story.append(Paragraph("Top 10 In-Demand Job Roles", section_style))
    story.append(ranking_table(
        "Job Role", "Postings",
        [(name, count) for name, count in top_roles.items()]
    ))

    # Job Listings Table (first 30 rows)
    story.append(Paragraph("Recent Job Listings (first 30)", section_style))
    story.append(Paragraph(
        "Showing up to 30 most recent postings from the filtered dataset.",
        small_style
    ))
    story.append(Spacer(1, 0.2 * cm))

    listing_cols = ["job_title", "company", "location", "industry"]
    listing_cols = [c for c in listing_cols if c in df.columns]
    listing_df   = df[listing_cols].head(30)

    header_labels = {
        "job_title": "Job Title",
        "company":   "Company",
        "location":  "Location",
        "industry":  "Industry",
    }
    col_widths = {
        "job_title": 5.5 * cm,
        "company":   4.5 * cm,
        "location":  3.0 * cm,
        "industry":  3.0 * cm,
    }

    tbl_header = [Paragraph(f"<b>{header_labels.get(c, c)}</b>", body_style) for c in listing_cols]
    tbl_data   = [tbl_header]
    for _, row in listing_df.iterrows():
        tbl_data.append([
            Paragraph(str(row.get(c, ""))[:60], body_style) for c in listing_cols
        ])

    tbl = Table(
        tbl_data,
        colWidths=[col_widths.get(c, 4 * cm) for c in listing_cols],
        repeatRows=1,
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
    ]))
    story.append(tbl)

    # Footer note
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "JobSeekAI · Live data from BDJobs.com · Auto-updated daily · "
        "Built with Streamlit & Python",
        small_style,
    ))

    # ── Build PDF ──────────────────────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
