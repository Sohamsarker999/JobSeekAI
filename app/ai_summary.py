"""
ai_summary.py — LLM-powered market intelligence via the Groq API.

Constructs a dynamic prompt from live analytics and returns an
executive-level market insight summary.

Also provides AI-powered job recommendations based on user profile.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
REQUEST_TIMEOUT = 30


def _get_api_key() -> str | None:
    """Retrieve the Groq API key from Streamlit secrets or environment."""
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY")


def _call_groq(messages: list, max_tokens: int = 512) -> str:
    """Low-level helper: sends messages to Groq and returns text response."""
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ GROQ_API_KEY not set."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(
            GROQ_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "⚠️ **Request Timed Out** — The AI service took too long. Please try again."
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "N/A"
        return f"⚠️ **API Error (HTTP {status})** — Check your API key and quota."
    except (requests.exceptions.RequestException, KeyError, IndexError):
        return "⚠️ **AI Unavailable** — Could not connect to Groq. Please try again shortly."


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------


def _build_prompt(
    top_skills: List[Tuple[str, int]],
    avg_salary: float,
    top_role: str,
    top_industry: str,
) -> str:
    """Create a structured prompt for the LLM from analytical summaries."""
    skills_str = ", ".join(f"{s} ({c})" for s, c in top_skills)

    salary_line = (
        f"• Average offered salary: BDT {avg_salary:,.0f}/month"
        if avg_salary and avg_salary > 0
        else "• Salary data: Most employers list salary as 'Negotiable'"
    )

    return f"""You are a senior labour-market analyst specialising in the
Bangladesh job market.

Based on the following real data extracted from recent job postings on
BDJobs.com (the largest job portal in Bangladesh), write a concise (~200 words)
executive market intelligence brief.

DATA SNAPSHOT
─────────────
- Top in-demand roles/requirements (with frequency): {skills_str}
{salary_line}
- Most common job role: {top_role}
- Dominant industry: {top_industry}

REQUIREMENTS
1. Open with a one-sentence market headline about Bangladesh job market.
2. Highlight 2-3 key hiring trends visible in this data.
3. Comment on which industries are hiring most aggressively.
4. Provide 2 actionable recommendations for job seekers in Bangladesh.
5. Close with a forward-looking outlook (1-2 sentences).

Write in a professional, data-driven tone suitable for an executive
dashboard. Avoid filler phrases. Be specific to Bangladesh context."""


# ---------------------------------------------------------------------------
# EXISTING FEATURE: Market Intelligence Summary
# ---------------------------------------------------------------------------

FALLBACK_MESSAGE = (
    "⚠️ **AI Summary Unavailable**\n\n"
    "Could not generate the market intelligence summary at this time. "
    "Please verify your `GROQ_API_KEY` environment variable is set and try again.\n\n"
    "You can still explore the analytics above."
)


def generate_market_summary(
    top_skills: List[Tuple[str, int]],
    salary_metrics: Dict[str, float | None],
    top_role: str,
    top_industry: str,
) -> str:
    """Call the Groq API and return a market-insight paragraph."""
    api_key = _get_api_key()
    if not api_key:
        return (
            "⚠️ **API Key Missing**\n\n"
            "Set the `GROQ_API_KEY` environment variable to enable "
            "AI-powered market summaries."
        )

    avg_salary = salary_metrics.get("mean") or 0.0
    prompt = _build_prompt(top_skills, avg_salary, top_role, top_industry)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise, data-driven labour-market analyst. "
                "Respond only with the requested brief — no preamble."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return _call_groq(messages, max_tokens=512)


# ---------------------------------------------------------------------------
# NEW FEATURE: AI-Powered Job Recommendations
# ---------------------------------------------------------------------------


def generate_job_recommendations(
    user_profile: str,
    df: pd.DataFrame,
    top_n: int = 5,
) -> list[dict]:
    """
    Match a user's skills/experience against scraped jobs using Groq AI.

    Parameters
    ----------
    user_profile : str
        Free-text description of the candidate's skills, experience, education.
    df : pd.DataFrame
        The full (or filtered) jobs dataframe from Google Sheets.
    top_n : int
        Number of top matches to return (default 5).

    Returns
    -------
    list[dict]  — each dict has keys:
        rank, job_title, company, location, industry, experience,
        deadline, match_score, reason
    On error, returns a list with a single dict containing an "error" key.
    """
    if df.empty:
        return [{"error": "No job data available to match against. Please check your data source."}]

    # ── Sample to keep the prompt size manageable ──────────────────────────
    sample_df = df.sample(min(80, len(df)), random_state=42).reset_index(drop=True)

    # ── Build a compact job catalogue for the prompt ───────────────────────
    lines = []
    for idx, row in sample_df.iterrows():
        title    = str(row.get("job_title", "N/A")).strip()
        company  = str(row.get("company",   "N/A")).strip()
        location = str(row.get("location",  "N/A")).strip()
        industry = str(row.get("industry",  "N/A")).strip()
        skills   = str(row.get("skills",    "N/A")).strip()
        lines.append(
            f"ID:{idx} | {title} @ {company} | Loc:{location} | "
            f"Industry:{industry} | Skills/Info:{skills[:120]}"
        )

    jobs_text = "\n".join(lines)

    # ── Prompt ─────────────────────────────────────────────────────────────
    prompt = f"""You are a career advisor specialising in the Bangladesh job market.

CANDIDATE PROFILE:
\"\"\"{user_profile}\"\"\"

AVAILABLE JOBS (format: ID | Title @ Company | Location | Industry | Skills/Info):
{jobs_text}

TASK:
Select the TOP {top_n} jobs that best match this candidate.
For each match return:
  - job_id   : the exact integer ID from the list above
  - match_score : integer 0-100
  - reason   : 1-2 sentences explaining the match

Return ONLY a valid JSON array — no markdown, no explanation outside the JSON.

Example format:
[
  {{"job_id": 3, "match_score": 91, "reason": "Your Python and SQL skills directly match the data analyst requirements."}},
  {{"job_id": 17, "match_score": 84, "reason": "..."}}
]"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a precise career-matching engine. "
                "Always reply with a valid JSON array only — no prose, no markdown fences."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    raw = _call_groq(messages, max_tokens=900)

    # ── Parse the JSON response ────────────────────────────────────────────
    try:
        clean = raw.strip()
        # Strip markdown code fences if the model adds them despite instructions
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.lower().startswith("json"):
                clean = clean[4:]
        matches = json.loads(clean.strip())
    except Exception:
        return [{"error": f"Could not parse AI response. Raw output:\n\n{raw}"}]

    if not isinstance(matches, list):
        return [{"error": "Unexpected response format from AI. Please try again."}]

    # ── Enrich with full job details from the dataframe ───────────────────
    results = []
    for rank, match in enumerate(matches[:top_n], start=1):
        job_id = match.get("job_id")
        try:
            row = sample_df.loc[int(job_id)]
        except (KeyError, TypeError, ValueError):
            continue  # skip if AI hallucinated a non-existent ID

        results.append({
            "rank":        rank,
            "job_title":   str(row.get("job_title",  "N/A")).strip(),
            "company":     str(row.get("company",    "N/A")).strip(),
            "location":    str(row.get("location",   "N/A")).strip(),
            "industry":    str(row.get("industry",   "N/A")).strip(),
            "experience":  str(row.get("skills",     "N/A")).strip()[:120],
            "deadline":    str(row.get("deadline",   "")).strip(),
            "match_score": int(match.get("match_score", 0)),
            "reason":      str(match.get("reason", "")).strip(),
        })

    if not results:
        return [{"error": "AI returned matches but none could be mapped to real jobs. Try again."}]

    return results
