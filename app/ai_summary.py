"""
ai_summary.py — LLM-powered market intelligence via the Groq API.

Features:
  - generate_market_summary()     : executive market brief
  - generate_job_recommendations(): AI job matching
  - analyze_skill_gap()           : skill gap analysis + readiness score
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
GROQ_MODEL   = "llama-3.3-70b-versatile"
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
        "model":      GROQ_MODEL,
        "messages":   messages,
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
    skills_str  = ", ".join(f"{s} ({c})" for s, c in top_skills)
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
# FEATURE 1: Market Intelligence Summary
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
    prompt     = _build_prompt(top_skills, avg_salary, top_role, top_industry)

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
# FEATURE 2: AI-Powered Job Recommendations
# ---------------------------------------------------------------------------


def generate_job_recommendations(
    user_profile: str,
    df: pd.DataFrame,
    top_n: int = 5,
) -> list[dict]:
    """
    Match a user's skills/experience against scraped jobs using Groq AI.
    Returns a list of dicts with rank, job details, match_score, reason.
    On error returns a list with a single dict containing an 'error' key.
    """
    if df.empty:
        return [{"error": "No job data available to match against."}]

    sample_df = df.sample(min(80, len(df)), random_state=42).reset_index(drop=True)

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

    prompt = f"""You are a career advisor specialising in the Bangladesh job market.

CANDIDATE PROFILE:
\"\"\"{user_profile}\"\"\"

AVAILABLE JOBS (format: ID | Title @ Company | Location | Industry | Skills/Info):
{jobs_text}

TASK:
Select the TOP {top_n} jobs that best match this candidate.
For each match return:
  - job_id      : the exact integer ID from the list above
  - match_score : integer 0-100
  - reason      : 1-2 sentences explaining the match

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

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.lower().startswith("json"):
                clean = clean[4:]
        matches = json.loads(clean.strip())
    except Exception:
        return [{"error": f"Could not parse AI response. Raw output:\n\n{raw}"}]

    if not isinstance(matches, list):
        return [{"error": "Unexpected response format from AI. Please try again."}]

    results = []
    for rank, match in enumerate(matches[:top_n], start=1):
        job_id = match.get("job_id")
        try:
            row = sample_df.loc[int(job_id)]
        except (KeyError, TypeError, ValueError):
            continue

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


# ---------------------------------------------------------------------------
# FEATURE 3: Skill Gap Analyzer
# ---------------------------------------------------------------------------


def _extract_market_skills(df: pd.DataFrame, top_n: int = 40) -> List[str]:
    """
    Pull the most frequently mentioned skills/keywords from the
    scraped jobs dataset. Used to build the 'market demand' side
    of the skill gap comparison.
    """
    from collections import Counter
    import re

    all_tokens: list[str] = []

    # Common stopwords to filter out so we get real skills, not noise
    STOPWORDS = {
        "the", "and", "or", "in", "of", "to", "a", "an", "is", "are",
        "for", "with", "on", "at", "by", "as", "be", "will", "we",
        "you", "not", "this", "that", "our", "from", "have", "has",
        "experience", "required", "minimum", "maximum", "years", "year",
        "job", "work", "candidate", "applicant", "position", "role",
        "company", "team", "good", "strong", "excellent", "knowledge",
        "ability", "skill", "skills", "must", "should", "prefer",
        "preferred", "graduate", "university", "degree", "education",
        "male", "female", "both", "any", "all", "other", "please",
        "apply", "salary", "negotiable", "attractive", "package",
        "bangladesh", "dhaka", "chittagong", "sylhet",
    }

    col = "skills" if "skills" in df.columns else None
    if col is None:
        return []

    for text in df[col].dropna().astype(str):
        # Tokenise: split on commas, slashes, pipes, semicolons, newlines
        tokens = re.split(r"[,/|;\n]+", text.lower())
        for token in tokens:
            token = token.strip()
            # Keep tokens that are 2-40 chars and not pure stopwords
            if 2 <= len(token) <= 40 and token not in STOPWORDS:
                all_tokens.append(token)

    counts  = Counter(all_tokens)
    top     = [skill for skill, _ in counts.most_common(top_n)]
    return top


def analyze_skill_gap(
    user_profile: str,
    df: pd.DataFrame,
) -> dict:
    """
    Compare the user's stated skills against live market demand and
    return a structured skill gap report.

    Parameters
    ----------
    user_profile : str
        Free-text description of the candidate's skills and background.
    df : pd.DataFrame
        The filtered jobs DataFrame.

    Returns
    -------
    dict with keys:
        readiness_score   : int 0–100
        score_label       : str  e.g. "Strong"
        score_color       : str  hex colour
        matched_skills    : list[str]   skills user has that market wants
        missing_critical  : list[dict]  {skill, reason, how_to_learn}
        missing_optional  : list[str]   nice-to-have gaps
        strengths         : list[str]   user's standout advantages
        top_roles         : list[str]   roles best suited to user right now
        summary           : str         2-3 sentence narrative
        error             : str | None
    """
    if df.empty:
        return {"error": "No job data available. Please check your data source."}

    if not user_profile.strip():
        return {"error": "Please enter your skills and background first."}

    # Pull market demand from scraped data
    market_skills = _extract_market_skills(df, top_n=40)
    if not market_skills:
        return {"error": "Could not extract market skills from dataset."}

    # Also get top roles and industries for context
    top_roles_list     = df["job_title"].value_counts().head(10).index.tolist()
    top_industry_list  = df["industry"].value_counts().head(6).index.tolist()

    market_skills_str  = ", ".join(market_skills)
    top_roles_str      = ", ".join(top_roles_list)
    top_industries_str = ", ".join(top_industry_list)

    prompt = f"""You are a senior career coach and skill gap analyst specialising
in the Bangladesh job market.

CANDIDATE PROFILE (what they currently have):
\"\"\"{user_profile}\"\"\"

LIVE MARKET DATA (extracted from {len(df)} real job postings on BDJobs.com):
- Most demanded skills/keywords: {market_skills_str}
- Most common job roles hiring right now: {top_roles_str}
- Top hiring industries: {top_industries_str}

TASK — Perform a thorough skill gap analysis. Return ONLY a valid JSON object
(no markdown fences, no explanation outside the JSON) with exactly these keys:

{{
  "readiness_score": <integer 0-100, how job-market-ready this candidate is>,
  "matched_skills": [<list of strings — skills the candidate has that the market wants>],
  "missing_critical": [
    {{
      "skill": "<skill name>",
      "reason": "<1 sentence: why this skill matters in BD market>",
      "how_to_learn": "<1 sentence: specific free resource or approach>"
    }}
  ],
  "missing_optional": [<list of strings — nice-to-have skills they lack>],
  "strengths": [<list of strings — candidate's standout advantages>],
  "top_roles": [<list of 3 job role titles from the market data that best fit this candidate RIGHT NOW>],
  "summary": "<2-3 sentence narrative overview of their market position>"
}}

RULES:
- missing_critical: list the 3-5 most impactful gaps only
- missing_optional: list up to 5 nice-to-have gaps
- matched_skills: list up to 8 matching skills
- strengths: list up to 4 genuine strengths
- Be specific to Bangladesh job market context
- how_to_learn must mention a specific free resource (Coursera, YouTube, freeCodeCamp, etc.)
- readiness_score: 80-100 = strong, 60-79 = good, 40-59 = developing, 0-39 = early stage"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a precise skill gap analysis engine for the Bangladesh job market. "
                "Always reply with a valid JSON object only — no prose, no markdown fences."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    raw = _call_groq(messages, max_tokens=1200)

    # Parse JSON
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.lower().startswith("json"):
                clean = clean[4:]
        result = json.loads(clean.strip())
    except Exception:
        return {"error": f"Could not parse AI response. Raw output:\n\n{raw}"}

    # Validate required keys are present
    required = [
        "readiness_score", "matched_skills", "missing_critical",
        "missing_optional", "strengths", "top_roles", "summary",
    ]
    for key in required:
        if key not in result:
            result[key] = [] if key != "readiness_score" else 50

    # Add score label and colour
    score = int(result.get("readiness_score", 50))
    if score >= 80:
        result["score_label"] = "Strong"
        result["score_color"] = "#16a34a"   # green
    elif score >= 60:
        result["score_label"] = "Good"
        result["score_color"] = "#2563eb"   # blue
    elif score >= 40:
        result["score_label"] = "Developing"
        result["score_color"] = "#d97706"   # amber
    else:
        result["score_label"] = "Early Stage"
        result["score_color"] = "#dc2626"   # red

    result["error"] = None
    return result
